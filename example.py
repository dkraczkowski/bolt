from bolt.application import ServiceLocator, bolt
from bolt.http import Request, Response


@bolt.route('/test')
class Controller:

    @bolt.get('/hello_world')
    def action_1(self, request: Request):
        return Response('Hello World')

bolt.run('0.0.0.0', 8800)
