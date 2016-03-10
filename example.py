from bolt.application import ServiceLocator, bolt
from bolt.http import Request, Response
from cherrypy import wsgiserver
from wsgiref import simple_server

class Validator:

    def username(self):
        pass



@bolt.route('/test')
class Controller:

    @bolt.get('/hello_world')
    def action_1(self, request: Request):

        return Response('Hello World')
'''
server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8800), bolt)
server.start()'''
httpd = simple_server.make_server('127.0.0.1', 8800, bolt)
httpd.serve_forever()
