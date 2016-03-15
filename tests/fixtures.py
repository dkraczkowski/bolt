from bolt.application import Bolt, ServiceLocator
from bolt.routing import Route
from bolt.validation import Validator, StringValidator, EmailValidator

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


class SimpleTestObject:
    def __init__(self):
        self.a = 0
        self.b = 0
        self.c = 0

    def test_method(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c


class ExampleValidator(Validator):

    username = StringValidator()
    password = StringValidator()
