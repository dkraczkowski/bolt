from bolt.application import bolt
from bolt.http import Request, Response
from bolt.validation import *
from cherrypy import wsgiserver


class UserDetails(Validator):
    username = EmailValidator(required=True)
    password = StringValidator(required=True, min=4)

@bolt.route('/')
class Controller:

    @bolt.get('/')
    def action_1(self, request: Request):
        return Response('Default Response')

    @bolt.post('/hello', validator=UserDetails)
    def hello_username(self):
        return Response('Hello World')

bolt.use(ValidationService())

server = wsgiserver.CherryPyWSGIServer(
    ('0.0.0.0', 8800),
    bolt.ready(),
    numthreads=32,
    request_queue_size=100
)
server.start()