import unittest
import inspect
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
        pass


class TestService:
    pass

def test_service_factory():
    return TestService()


@app.service(TestService)
def test_service_factory(service_locator):
    return TestService()


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
        service = app.service_locator.get(TestService.__name__)
        #self.assertIsInstance(service, TestService)


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
