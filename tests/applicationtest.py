import unittest
from bolt.application import MiddlewareComposer, ControllerResolver, ServiceLocator, Bolt
from bolt.routing import Route
from bolt.utils import get_fqn

app = Bolt()


@app.route('/sample')
class SampleController:

    @app.get('/get-route')
    def some_action(self):
        pass

    @app.post('/other-action')
    def other_action(self):
        pass

    @app.post('/{id:numeric}')
    def action_0(self):
        return 69


class TestService:
    def __init__(self):
        self.meaning_of_life = 42
    pass


class DependedService:
    def __init__(self, dependency: TestService):
        self.dependency = dependency


def test_service_factory():
    return TestService()


@app.service(TestService)
def test_service_factory(service_locator):
    return TestService()


@app.service(DependedService)
def depended_service(service_locator: ServiceLocator):
    return DependedService(service_locator.get(TestService))


@app.route('/dependencies')
class ControllerWithDependencies:
    def __init__(self, service: DependedService):
        self.service = service

    @app.get('/{id:numeric}')
    def action_0(self, route: Route):
        return int(route.params['id']) + self.service.dependency.meaning_of_life


class ServiceLocatorTest(unittest.TestCase):
    def test_set(self):
        sl = ServiceLocator()
        sl.set(TestService)

        self.assertEqual(sl._services_definitions[get_fqn(TestService)], TestService)

    def test_get(self):
        sl = ServiceLocator()
        sl.set(TestService)
        self.assertEqual(sl.get(get_fqn(TestService)), TestService)

    def test_get_by_alias(self):
        sl = ServiceLocator()
        sl.set(TestService)
        self.assertEqual(sl.get(TestService), TestService)

    def test_get_by_class(self):
        sl = ServiceLocator()
        sl.set(TestService)
        self.assertEqual(sl.get(TestService), TestService)

    def test_with_strategy(self):
        sl = ServiceLocator()
        sl.set(test_service_factory, TestService)
        serviceInstance = sl.get(TestService)
        self.assertIsInstance(serviceInstance, TestService)

    def test_with_assigned_name(self):
        sl = ServiceLocator()
        sl.set(test_service_factory, 'CustomName')
        serviceInstance = sl.get('CustomName')
        self.assertIsInstance(serviceInstance, TestService)


class ApplicationFoundationTest(unittest.TestCase):

    def test_expose(self):
        app._build_route_map()
        route = app._map.find('/sample/other-action')
        self.assertIsInstance(route, Route)

    def test_service(self):
        service = app.service_locator.get(TestService)
        self.assertIsInstance(service, TestService)

    def test_service_resolvance(self):
        test_service = app.service_locator.get(TestService)
        depended_service = app.service_locator.get(DependedService)

        self.assertIsInstance(depended_service, DependedService)
        self.assertEqual(depended_service.dependency, test_service)


class ControllerResolverTest(unittest.TestCase):
    def test_resolve(self):
        route = app._map.find('/sample/11')
        controller_resolver = ControllerResolver(route, app.service_locator)
        result = controller_resolver.resolve()

        self.assertEqual(69, result)

    def test_resolve_with_dependencies(self):
        route = app._map.find('/dependencies/33')
        controller_resolver = ControllerResolver(route, app.service_locator)
        result = controller_resolver.resolve()

        self.assertEqual(75, result)


class MiddlewareComposerTest(unittest.TestCase):

    def test_middleware(self):
        def a(b):
            self.assertEqual(2, b)

        def b(p):
            self.assertEqual(1, p)

        def c(u=3):
            self.assertEqual(3, u)

        def d(a, b):
            self.assertEqual(2, a)
            self.assertEqual(3, b)

        middleware = MiddlewareComposer()
        middleware.add(a).add(b).add(c)

        self.assertTrue(middleware(p=1, b=2, c=3))

        middleware = MiddlewareComposer()
        middleware.add(a).add(d)

        self.assertTrue(middleware(2, 3))