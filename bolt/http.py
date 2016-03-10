from urllib.parse import urlparse
from six.moves.http_cookies import SimpleCookie


class HttpBody:
    def __init__(self, stream, length):
        self.stream = stream
        self.length = length
        self._bytes_remaining = length
        self._contents = ""

    @property
    def contents(self):
        if self._bytes_remaining > 0:
            self.read()
        return self._contents

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.stream)

    next = __next__

    def read(self, size=None):
        buffer = self._read(self.stream.read, size)
        self._contents += buffer.decode("utf-8")
        return buffer


    def readline(self, limit=None):
        return self._read(self.stream.readline)

    def _read(self, reader, size=None):
        if size is None or size == -1 or size > self._bytes_remaining:
            size = self._bytes_remaining
        self._bytes_remaining -= size
        return reader(size)


class HttpMessage:
    WSGI_CONTENT_HEADERS = ('CONTENT_TYPE', 'CONTENT_LENGTH')
    TRUE_STRINGS = ('true', 'True', 'yes')
    FALSE_STRINGS = ('false', 'False', 'no')

    @property
    def body(self):
        return self._body

    def __init__(self, body, headers=None):
        self._headers = headers
        self._body = body

    def headers(self, name: str):
        """
        Case insensitive
        :param name:
        :return:
        """
        name = name.upper().replace('-', '_')
        if name in self._headers:
            return self._headers[name]

        return None


class Request(HttpMessage):

    METHOD_HEAD = 'HEAD'
    METHOD_GET = 'GET'
    METHOD_POST = 'POST'
    METHOD_PUT = 'PUT'
    METHOD_PATCH = 'PATCH'
    METHOD_DELETE = 'DELETE'
    METHOD_PURGE = 'PURGE'
    METHOD_OPTIONS = 'OPTIONS'
    METHOD_TRACE = 'TRACE'
    METHOD_CONNECT = 'CONNECT'

    @property
    def uri(self):
        return self._uri

    @property
    def cookies(self):
        if self._cookies is None:
            parser = SimpleCookie(self.headers("Cookie"))
            cookies = {}
            for morsel in parser.values():
                cookies[morsel.key] = morsel.value

            self._cookies = cookies

        return self._cookies.copy()

    @property
    def files(self):
        return self._files

    @property
    def method(self):
        return self._method

    def __init__(self, method, uri, body, headers=None):
        super().__init__(body, headers)
        self._method = method
        self._uri = uri
        self._cookies = None

    @staticmethod
    def from_env(env):
        headers = {}
        for key in env:
            if key.startswith('HTTP'):
                headers[key[5:]] = env[key]
            elif key in HttpMessage.WSGI_CONTENT_HEADERS:
                headers[key] = env[key]

        uri = Uri.from_env(env)
        if 'CONTENT_LENGTH' in env and int(env['CONTENT_LENGTH']) > 0:
            body = HttpBody(env['wsgi.input'], int(env['CONTENT_LENGTH']))
        else:
            body = None

        request = Request(env['REQUEST_METHOD'], uri, body, headers)
        return request


class Response(HttpMessage):

    HTTP_CONTINUE = 100
    HTTP_SWITCHING_PROTOCOLS = 101
    HTTP_PROCESSING = 102
    HTTP_OK = 200
    HTTP_CREATED = 201
    HTTP_ACCEPTED = 202
    HTTP_NON_AUTHORITATIVE_INFORMATION = 203
    HTTP_NO_CONTENT = 204
    HTTP_RESET_CONTENT = 205
    HTTP_PARTIAL_CONTENT = 206
    HTTP_MULTI_STATUS = 207
    HTTP_ALREADY_REPORTED = 208
    HTTP_IM_USED = 226
    HTTP_MULTIPLE_CHOICES = 300
    HTTP_MOVED_PERMANENTLY = 30
    HTTP_FOUND = 302
    HTTP_SEE_OTHER = 303
    HTTP_NOT_MODIFIED = 304
    HTTP_USE_PROXY = 305
    HTTP_RESERVED = 306
    HTTP_TEMPORARY_REDIRECT = 307
    HTTP_PERMANENTLY_REDIRECT = 308
    HTTP_BAD_REQUEST = 400
    HTTP_UNAUTHORIZED = 401
    HTTP_PAYMENT_REQUIRED = 402
    HTTP_FORBIDDEN = 403
    HTTP_NOT_FOUND = 404
    HTTP_METHOD_NOT_ALLOWED = 405
    HTTP_NOT_ACCEPTABLE = 406
    HTTP_PROXY_AUTHENTICATION_REQUIRED = 407
    HTTP_REQUEST_TIMEOUT = 408
    HTTP_CONFLICT = 409
    HTTP_GONE = 410
    HTTP_LENGTH_REQUIRED = 411
    HTTP_PRECONDITION_FAILED = 412
    HTTP_REQUEST_ENTITY_TOO_LARGE = 413
    HTTP_REQUEST_URI_TOO_LONG = 414
    HTTP_UNSUPPORTED_MEDIA_TYPE = 415
    HTTP_REQUESTED_RANGE_NOT_SATISFIABLE = 416
    HTTP_EXPECTATION_FAILED = 417
    HTTP_I_AM_A_TEAPOT = 418
    HTTP_UNPROCESSABLE_ENTITY = 422
    HTTP_LOCKED = 423
    HTTP_FAILED_DEPENDENCY = 424
    HTTP_RESERVED_FOR_WEBDAV_ADVANCED_COLLECTIONS_EXPIRED_PROPOSAL = 425
    HTTP_UPGRADE_REQUIRED = 426
    HTTP_PRECONDITION_REQUIRED = 428
    HTTP_TOO_MANY_REQUESTS = 429
    HTTP_REQUEST_HEADER_FIELDS_TOO_LARGE = 43
    HTTP_INTERNAL_SERVER_ERROR = 500
    HTTP_NOT_IMPLEMENTED = 501
    HTTP_BAD_GATEWAY = 502
    HTTP_SERVICE_UNAVAILABLE = 503
    HTTP_GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    HTTP_VARIANT_ALSO_NEGOTIATES_EXPERIMENTAL = 506
    HTTP_INSUFFICIENT_STORAGE = 507
    HTTP_LOOP_DETECTED = 508
    HTTP_NOT_EXTENDED = 510
    HTTP_NETWORK_AUTHENTICATION_REQUIRED = 511

    @property
    def status(self):
        return self._status

    def __init__(self, body, status=200, headers=None):
        self._body = body
        self._status = status
        pass


class Uri:
    """
    Uri structure:

                    hierarchical part
          ┌───────────────────┴─────────────────────┐
                      authority               path
          ┌───────────────┴───────────────┐┌───┴────┐
    abc://username:password@example.com:123/path/data?key=value#fragid1
    └┬┘   └───────┬───────┘ └────┬────┘ └┬┘           └───┬───┘ └──┬──┘
    scheme  user information     host     port            query   fragment

    urn:example:mammal:monotreme:echidna
    └┬┘ └──────────────┬───────────────┘
    scheme            path
    @source: https://en.wikipedia.org/wiki/Uniform_Resource_Identifie
    """

    SCHEME_HTTP = 'http'
    SCHEME_HTTPS = 'https'

    @property
    def scheme(self):
        return self._scheme

    @property
    def port(self):
        return self._port

    @property
    def hostname(self):
        return self._hostname

    @property
    def path(self):
        return self._path

    def __init__(self, uri: str):
        parts = urlparse(uri)
        self._scheme = parts.scheme
        self._port = parts.port
        self._hostname = parts.hostname
        self._path = parts.path
        self._query = parts.query
        self._fragment = parts.fragment
        self._username = parts.username
        self._password = parts.password

    @classmethod
    def from_env(cls, env):
        host = env['HTTP_HOST'].split(':')
        instance = Uri('')
        instance._scheme = env['wsgi.url_scheme']
        instance._hostname = host[0]
        try :
            instance._port = host[1]
        except IndexError:
            if instance._scheme == Uri.SCHEME_HTTP:
                instance._port = 80
            else:
                instance._port = 443
        instance._path = env['PATH_INFO']
        instance._query = env['QUERY_STRING']
        return instance


class HttpException(Exception):
    pass
