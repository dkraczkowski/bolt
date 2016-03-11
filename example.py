from bolt.application import bolt
from bolt.http import Request, Response
from cherrypy import wsgiserver

@bolt.before()
def do_something_with_request(request: Request):
    pass

@bolt.after()
def after_middleware(request: Request, response: Response):
    response._body += 'a'

@bolt.route('/')
class Controller:

    @bolt.get('/hello')
    def action_1(self, request: Request):

        return Response('Hello World')


server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8800), bolt.ready(), numthreads=32, request_queue_size=100)
server.start()
'''
httpd = simple_server.make_server('127.0.0.1', 8800, bolt.ready())
httpd.serve_forever()'''
