"""
Bolt is a micro rest framework.

Copyright (c) 2016, Dawid Krac Kraczkowski
License: MIT (see LICENSE for details)
"""
from .routing import Route, RouteMap
from .utils import find_class, get_fqn, call_object_method, find_clsname
import inspect
import copy


class ApplicationFoundation:

    def __init__(self):
        self._map = RouteMap()
        self._before_middleware = MiddlewareComposer()
        self._after_middleware = MiddlewareComposer()
        self.service_locator = ServiceLocator()
        self._base_routes = {}
        self._routes = []
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

    def get(self, rule: str):
        """ Connects an URI rule to GET request.
        :param rule: uri rule
        """
        def decorator(func):
            self.expose(rule, func, ['GET'])

            return func

        return decorator

    def post(self, rule: str):
        def decorator(func):
            self.expose(rule, func, ['POST'])

            return func

        return decorator

    def put(self, rule: str):
        def decorator(func):
            self.expose(rule, func, ['PUT'])

            return func

        return decorator

    def patch(self, rule: str):
        def decorator(func):
            self.expose(rule, func, ['PATCH'])

            return func

        return decorator

    def delete(self, rule: str):
        def decorator(func):
            self.expose(rule, func, ['DELETE'])

            return func

        return decorator

    def options(self, rule: str):
        def decorator(func):
            self.expose(rule, func, ['OPTIONS'])

            return func

        return decorator

    def any(self, rule: str):
        def decorator(func):
            self.expose(rule, func)

            return func

        return decorator

    def expose(self, rule, func, method=None):
        if method is None:
            method = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']

        self._routes.append({
            'rule': rule,
            'func': func,
            'method': method
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
                rule = self._base_routes[clsname] + rule

            self._map.add(Route(rule, func), route['method'])


class Bolt(ApplicationFoundation):

    VERSION = '0.1.0'

    def __call__(self, env, start_response):
        return self._on_request(start_response, env)

    def _on_request(self, start_response, env):
        pass

    def _on_error(self, request, response, error: Exception):
        pass


class ServiceLocator:
    """ ServiceLocator
    """
    def __init__(self):
        self._services_definitions = {}
        self._services = {}

    def set(self, service, name=None):
        """ Registers new service in service locator, if no name provided
        ServiceLocator will resolve service's name automatically, using
        following schema:

            moduleNameOfService + "." + service.__name__

        :param service: service
        :param name: service's name (not required)
        :return:
        """
        if name is None:
            name = get_fqn(service)

        elif not isinstance(name, str):
            name = get_fqn(name)

        self._services_definitions[name] = service

    def get(self, name):
        """ Resolves the name to already registered service, if service was already instantiated
        this will return its instance otherwise it will try to instantiate the service
        :param name: previously registered service's name
        :return:
        """
        if inspect.isclass(name):
            name = get_fqn(name)

        if name in self._services_definitions:
            if name not in self._services:
                if inspect.isfunction(self._services_definitions[name]):
                    self._services[name] = self._services_definitions[name](self)
                else:
                    self._services[name] = self._services_definitions[name]

        else:
            return None

        return self._services[name]

    def destroy(self):
        """ Destroys all instantiated services
        :return:
        """
        self._services = {}

    def from_self(self):
        """ Creates new instance of ServiceLocator with already defined services'
        definitions.
        :return:
        """
        sl = copy.copy(self)
        sl.destroy()

        return sl


class ControllerResolver:
    def __init__(self, route: Route, service_locator: ServiceLocator):
        self.controller_class = find_class(route.callback)
        self.service_locator = service_locator.from_self()
        self.service_locator.set(route, Route)
        self.controller_method = route.callback

    def _resolve_constructor_dependencies(self):
        params = inspect.signature(self.controller_class.__init__).parameters.values()
        return self._resolve_params(params)

    def _resolve_method_dependencies(self):
        params = inspect.signature(self.controller_method).parameters.values()
        return self._resolve_params(params)

    def resolve(self):
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
            try:
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
            except Exception as e:
                self.error = e
                return False

        return True

bolt = Bolt()
