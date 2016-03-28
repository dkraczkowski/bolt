import unittest
from bolt.application import MiddlewareComposer, ControllerResolver, ServiceLocator, Bolt
from bolt.router import Route
from bolt.utils import get_fqn
from tests.fixtures import TestService, DependedService, test_service_factory, app


class ServiceLocatorTest(unittest.TestCase):
    def test_set(self):
        sl = ServiceLocator()
        sl.set(TestService)

        self.assertEqual(sl._services_definitions[get_fqn(TestService)], TestService)

    def test_get(self):
        sl = ServiceLocator()
        sl.set(TestService)
        self.assertEqual(sl.get(get_fqn(TestService)).__class__, TestService)

    def test_get_by_alias(self):
        sl = ServiceLocator()
        sl.set(TestService)
        self.assertEqual(sl.get(TestService).__class__, TestService)

    def test_get_by_class(self):
        sl = ServiceLocator()
        sl.set(TestService)
        self.assertEqual(sl.get(TestService).__class__, TestService)

    def test_with_strategy(self):
        sl = ServiceLocator()
        sl.set(test_service_factory, TestService)
        service_instance = sl.get(TestService)
        self.assertIsInstance(service_instance, TestService)

    def test_with_assigned_name(self):
        sl = ServiceLocator()
        sl.set(test_service_factory, 'CustomName')
        service_instance = sl.get('CustomName')
        self.assertIsInstance(service_instance, TestService)


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
        self.assertEqual(depended_service.dependency.__class__, test_service.__class__)


class ControllerResolverTest(unittest.TestCase):
    def test_resolve(self):
        route = app._map.find('/sample/11')
        controller_resolver = ControllerResolver(route.callback, app.service_locator)
        result = controller_resolver.resolve()

        self.assertEqual(69, result)

    def test_resolve_with_dependencies(self):
        route = app._map.find('/dependencies/33')
        sl = app.service_locator.from_self()
        sl.set(route, Route)
        controller_resolver = ControllerResolver(route.callback, app.service_locator)
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
