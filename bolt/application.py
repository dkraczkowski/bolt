"""
Bolt is a micro rest framework.

Copyright (c) 2016, Dawid Krac Kraczkowski
License: MIT (see LICENSE for details)
"""
from .router import Route, RouteMap
from .utils import find_class, get_fqn, call_object_method, find_clsname
from .http import Request, Response, HttpException
from .odm import Serializable

import inspect
import copy
import json


class ApplicationFoundation:

    def __init__(self):
        self._map = RouteMap()
        self._before_middleware = MiddlewareComposer()
        self._after_middleware = MiddlewareComposer()
        self.service_locator = ServiceLocator()
        self._base_routes = {}
        self._routes = []
        self._services = []
        pass

    def before(self):
        """ Middleware decorator. Creates middleware queue which is
        executed once the request is obtained but not yet passed
        to controller.
        """
        def decorator(func):
            self._before_middleware.add(func)
            return func

        return decorator

    def after(self):
        """ Middleware decorator. Creates middleware queue which is
        executed once the request has been processed by controller but
        the response has not yet being sent to client.
        """
        def decorator(func):
            self._after_middleware.add(func)
            return func

        return decorator

    def route(self, rule: str):
        def decorator(cls):
            self._base_routes[get_fqn(cls)] = rule
            return cls

        return decorator

    def get(self, rule: str, **kwargs):
        """ Connects an URI rule to GET request.
        :param rule: uri rule
        """
        def decorator(func):
            self.expose(rule, func, ['GET'], kwargs)

            return func

        return decorator

    def post(self, rule: str, **kwargs):
        def decorator(func):
            self.expose(rule, func, ['POST'], kwargs)
            return func

        return decorator

    def put(self, rule: str, **kwargs):
        def decorator(func):
            self.expose(rule, func, ['PUT'], kwargs)

            return func

        return decorator

    def patch(self, rule: str, **kwargs):
        def decorator(func):
            self.expose(rule, func, ['PATCH'], kwargs)

            return func

        return decorator

    def delete(self, rule: str, **kwargs):
        def decorator(func):
            self.expose(rule, func, ['DELETE'], kwargs)

            return func

        return decorator

    def options(self, rule: str, **kwargs):
        def decorator(func):
            self.expose(rule, func, ['OPTIONS'], kwargs)

            return func

        return decorator

    def any(self, rule: str, **kwargs):
        def decorator(func):
            self.expose(rule, func, None, kwargs)

            return func

        return decorator

    def expose(self, rule, func, method=None, settings=None):
        if method is None:
            method = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']

        self._routes.append({
            'rule': rule,
            'func': func,
            'method': method,
            'settings': settings
        })

    def service(self, name: str=None):
        def decorator(service):
            self.service_locator.set(service, name)
            return service
        return decorator

    def _build_route_map(self):
        for route in self._routes:
            rule = route['rule']
            func = route['func']
            clsname = find_clsname(func)

            if clsname and clsname in self._base_routes:
                if self._base_routes[clsname] is not '/':
                    rule = self._base_routes[clsname] + rule

            # Skip last /
            if rule[-1] == '/' and len(rule) > 1:
                rule = rule[:-1]

            self._map.add(Route(rule, func, route['settings']), route['method'])


class Bolt(ApplicationFoundation):

    VERSION = '0.1.0'

    def __init__(self):
        super().__init__()
        self._server = None

    def __call__(self, env, start_response):
        return self._on_request(env, start_response)

    def ready(self):
        self._build_route_map()
        for service in self._services:
            if hasattr(service, '__call__'):
                service(self)
        return self

    def use(self, service):
        self._services.append(service)

    def _on_request(self, env, start_response):
        request = Request.from_env(env)
        route = self._map.find(request.uri.path, [request.method])
        if route is None:
            if self._map.find(request.uri.path):
                return self._on_error(
                    request,
                    HttpException(
                        'Method not allowed',
                        Response.HTTP_METHOD_NOT_ALLOWED
                    ),
                    start_response
                )
            return self._on_error(request, HttpException('Not Found', Response.HTTP_NOT_FOUND), start_response)
        request.route = route
        service_locator = self.service_locator.from_self()
        service_locator.set(route, Route)
        service_locator.set(request, Request)
        resolver = ControllerResolver(route.callback, service_locator)

        try:
            self._before_middleware(service_locator)
            response = resolver.resolve()

            if not isinstance(response, Response):
                if response is str:
                    response = Response(response, 200)
                else:
                    raise HttpException(
                        'Controller returned unexpected value, expecting instance of %s or str' %
                        get_fqn(Response), Response.HTTP_SERVICE_UNAVAILABLE
                    )
            service_locator.set(response, Response)
            self._after_middleware(service_locator)
            start_response(Response.status_message(response.status), response.headers)
            return [response.body.encode("utf-8")]
        except HttpException as e:
            return self._on_error(request, e, start_response)

    def _on_error(self, request, error: HttpException, start_response):
        status_message = Response.status_message(error.code)
        response_contents = str(error).encode("utf-8")
        start_response(status_message, [('Content-Type', 'text/plain')])
        return [response_contents]


class ServiceLocator:
    """ ServiceLocator
    """
    def __init__(self):
        self._services_definitions = {}
        self._services = {}

    def set(self, service, name=None):
        """ Registers new service in service locator.

        If no name will be provided ServiceLocator will use service's fully qualified name:
            moduleNameOfService + "." + service.__name__

        If class will be provided as a service name, ServiceLocator will use its
        fully qualified name as a name.

        Service can be anything, there are different behaviours assigned to different types
        of services. See ServiceLocator.get for more information.

        :param service: service
        :param name: service's name (not required) can be string or class
        :return:
        """
        if name is None:
            name = get_fqn(service)

        elif not isinstance(name, str):
            name = get_fqn(name)

        self._services_definitions[name] = service

    def get(self, name):
        """ Resolves the name to a registered service.
        If registered service is a class, ServiceLocator will try to create its
        instance and resolve all its dependencies. If it fails AttributeError exception
        will be thrown. Instance will be persisted for later use and every time
        ServiceLocator.get is called with the same service's name the instance will be
        returned.

        If registered service is a function, ServiceLocator will call it and return that
        function's results (note that ServiceLocator's instance will be passed to the function).

        In any other scenario service locator will just return registered object.

        :param name: service's name
        :return:
        """
        if inspect.isclass(name):
            name = get_fqn(name)

        if name in self._services_definitions:
            service = self._services_definitions[name]
            if name not in self._services:
                if inspect.isfunction(service):
                    return service(self)
                elif inspect.isclass(service):
                    self._services[name] = self._resolve_service(service)
                else:
                    return service
        else:
            return None

        return self._services[name]

    def destroy(self):
        """ Destroys all instantiated services
        :return:
        """
        self._services = {}

    def from_self(self) -> 'ServiceLocator':
        """ Creates and returns new copy of ServiceLocator from current instance.
        Note that all instantiated services will not be available in the ServiceLocator's
        copy.
        :return:
        """
        sl = copy.copy(self)
        sl.destroy()

        return sl

    def _resolve_service(self, service):
        constructor_params = inspect.signature(service.__init__).parameters.values()
        kwargs = {}
        for param in constructor_params:
            if param.name is 'self':
                continue
            if param.name is 'args':
                continue
            if param.name is 'kwargs':
                continue

            fqn = get_fqn(param.annotation)
            if fqn.startswith('builtins.'):
                continue
            dependency = self.get(fqn)
            if dependency is None:
                raise AttributeError('Could not resolve service %s' % fqn)
            kwargs[param.name] = dependency
        instance = service(**kwargs)
        return instance


class ControllerResolver:
    """ Takes responsibility for resolving controller's dependencies. If controller is a method
    it will create instance of appropriate class and call the method in the context of the class.

    All class and method dependencies will be resolved using service locator passed to the constructor.
    """
    def __init__(self, controller, service_locator: ServiceLocator):
        """
        Instantiate ControllerResolver

        :param controller: function or method
        :param service_locator: ServiceLocator
        :return:
        """
        self.controller_class = find_class(controller)
        self.service_locator = service_locator
        self.controller_method = controller

    def _resolve_constructor_dependencies(self):
        """
        If controller is a method its class constructor dependencies have to be resolved before
        the instance is created. This method takes care about resolving those dependencies.
        :return:
        """
        params = inspect.signature(self.controller_class.__init__).parameters.values()
        return self._resolve_params(params)

    def _resolve_method_dependencies(self):
        params = inspect.signature(self.controller_method).parameters.values()
        return self._resolve_params(params)

    def resolve(self):
        """
        Resolves constructor and returns results returned by controller
        :return:
        """
        instance = None
        if self.controller_class is not None:
            constructor_params = self._resolve_constructor_dependencies()
            if constructor_params:
                instance = self.controller_class(**constructor_params)
            else:
                instance = self.controller_class()

        method_dependencies = self._resolve_method_dependencies()

        if instance is None:
            if method_dependencies:
                return self.controller_method(**method_dependencies)
            else:
                return self.controller_method()

        if method_dependencies:
            return call_object_method(instance, self.controller_method.__name__, **method_dependencies)
        else:
            return call_object_method(instance, self.controller_method.__name__)

    def _resolve_params(self, params):
        resolved = {}
        for param in params:

            if param.name is 'self':
                continue
            if param.name is 'args':
                continue
            if param.name is 'kwargs':
                continue

            dependency = get_fqn(param.annotation)
            if dependency.startswith('builtins.'):
                continue

            resolved[param.name] = self.service_locator.get(dependency)

        return resolved


class MiddlewareComposer:

    def __init__(self):
        self._middleware = []
        self.error = None

    def add(self, middleware: callable):
        self._middleware.append(middleware)

        return self

    def __call__(self, *args, **kwargs):
        for callback in self._middleware:
            func_parameters = inspect.signature(callback).parameters
            kw_func_args = {}
            func_args = []
            if bool(kwargs):
                for name in func_parameters:
                    param = func_parameters[name]
                    if name in kwargs:
                        kw_func_args[name] = kwargs[name]
                    elif param.default:
                        kw_func_args[name] = param.default
                    else:
                        raise ValueError('Callable %s expects parameter %s to be passed, none given' % (
                                         callback.__name__, name))
            args_to_pass = len(func_parameters) - len(kw_func_args)
            if args_to_pass > 0:
                func_args = args[:args_to_pass]

            callback(*func_args, **kw_func_args)

        return True


class Controller:
    def send(self, obj, serializer='json', status=200):
        if not isinstance(obj, Serializable):
            if isinstance(obj, str):
               return Response(obj, status, {'Content-Type': 'text/plain'})
            raise ValueError('Passed object is not serializable')
        dict = obj.serialize()
        return Response(json.dumps(dict), status, {'Content-Type': 'text/json'})

bolt = Bolt()
