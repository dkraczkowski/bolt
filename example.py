from bolt.application import bolt
from bolt.http import Request, Response


@bolt.route('/test')
class Controller:

    @bolt.post('/hello_world')
    def action_1(self, request: Request):
        return Response('Hello World')

bolt.run('0.0.0.0', 8800)
