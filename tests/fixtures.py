from bolt.application import Bolt, ServiceLocator
from bolt.router import Route
from bolt.validator import Validator, StringValidator, EmailValidator
from bolt.odm import Field, Entity, Map
from datetime import datetime

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

    username = EmailValidator()
    password = StringValidator(min=3)


class UserEntity(Entity):
    name = Field(type=str)
    number = Field(type=int, default=0)
    height = Field(type=float)


class TeamEntity(Entity):
    name = Field(type=str, default='default')
    stars = Field(type=int)
    created_at = Field(type=datetime)
    creator = Field(type=UserEntity)
    scores = Field(type=list)
    members = Field(type=UserEntity)


class EntityA(Entity):
    value = Field(type=str)


class EntityB(Entity):
    value = Field(type=str)


class EntityC(Entity):
    value = Field(type=str)


class GroupEntity(Entity):
    group = Map(map={
        'a': EntityA,
        'b': EntityB,
        'c': EntityC
    }, discriminator='type')

