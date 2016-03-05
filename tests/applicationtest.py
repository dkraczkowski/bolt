import unittest
import inspect
from bolt.application import MiddlewareComposer, ControllerResolver, ServiceLocator, Bolt
from bolt.routing import Route

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


@app.service()
def test_service_factory(service_locator):
    return TestService()


class TestApplicationFoundation(unittest.TestCase):

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
