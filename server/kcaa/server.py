import SimpleHTTPServer
import SocketServer
import json
import logging
import os
import traceback
import urlparse


DEPLOYED_PACKAGE = 'build'
DEVELOPMENT_PACKAGE = 'web'


class KcaaHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    GET_NEW_OBJECTS = '/get_new_objects'
    GET_OBJECT = '/get_object'
    CLIENT_PREFIX = '/client/'

    def do_HEAD(self):
        self.dispatch()

    def do_GET(self):
        self.dispatch()

    def log_message(self, format, *args):
        # Kill verbose HTTP logging.
        return

    def dispatch(self):
        o = urlparse.urlparse(self.path)
        if o.path == KcaaHTTPRequestHandler.GET_NEW_OBJECTS:
            self.handle_get_new_objects(o)
        elif o.path == KcaaHTTPRequestHandler.GET_OBJECT:
            self.handle_get_object(o)
        elif o.path.startswith(KcaaHTTPRequestHandler.CLIENT_PREFIX):
            self.handle_client(o)
        else:
            self.send_error(404, 'Unknown handler: {}'.format(self.path))

    def handle_get_new_objects(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/json; charset=UTF-8')
        self.end_headers()
        self.wfile.write(json.dumps(list(self.server.new_objects)))

    def handle_get_object(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        queries = urlparse.parse_qs(o.query)
        try:
            object_type = queries['type']
            if len(object_type) > 1:
                self.send_error(400, 'Parameter type should have only 1 value')
                return
            object_type = object_type[0]
        except KeyError:
            self.send_error(400, 'Missing parameter: type')
            return
        try:
            data = self.server.objects[object_type]
            self.server.new_objects.remove(object_type)
            self.send_response(200)
            self.send_header('Content-Type', 'text/json; charset=UTF-8')
            self.end_headers()
            self.wfile.write(data)
        except KeyError:
            self.send_error(404)

    def handle_client(self, o):
        self.path = '/' + o.path[len(KcaaHTTPRequestHandler.CLIENT_PREFIX):]
        # Note: HTTP request handlers are not new-style classes.
        # super() cannot be used.
        if self.command == 'HEAD':
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_HEAD(self)
        elif self.command == 'GET':
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.send_error(501, 'Unknown method: {}'.format(self.command))


def move_to_client_dir():
    # Change directory to client directory so that SimpleHTTPServer can serve
    # client resources.
    client_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                              '..', 'client'))
    if not os.path.isdir(client_dir):
        raise IOError('No client directory found: {}'.format(client_dir))
    os.chdir(client_dir)
    # Use 'build' subdirectory when deployed, or 'web' when being developed.
    if os.path.isdir(DEPLOYED_PACKAGE):
        os.chdir(DEPLOYED_PACKAGE)
    elif os.path.isdir(DEVELOPMENT_PACKAGE):
        os.chdir(DEVELOPMENT_PACKAGE)
    else:
        raise IOError('No client package directories found under {}.'.format(
            client_dir))


def setup(args, logger):
    move_to_client_dir()
    httpd = SocketServer.TCPServer(('', args.server_port),
                                   KcaaHTTPRequestHandler)
    _, port = httpd.server_address
    # Don't use query (something like ?key=value). Kancolle widget detects it
    # from referer and rejects to respond.
    root_url = 'http://localhost:{}/client/'.format(port)
    logger.info('KCAA server ready at {}'.format(root_url))
    return httpd, root_url


def handle_server(args, controller_conn, to_exit):
    try:
        logger = logging.getLogger('kcaa.server')
        # Wait until the controller reset the proxy.
        if not controller_conn.poll(12.0):
            logger.error('Controller couldn\'t reset the proxy. '
                         'Shutting down.')
            to_exit.set()
            return
        assert controller_conn.recv()
        httpd, root_url = setup(args, logger)
        httpd.new_objects = set()
        httpd.objects = {}
        controller_conn.send(root_url)
        httpd.timeout = 0.1
        while True:
            httpd.handle_request()
            if to_exit.wait(0.0):
                logger.info('Server got an exit signal. Shutting down.')
                break
            while controller_conn.poll():
                object_type, data = controller_conn.recv()
                httpd.new_objects.add(object_type)
                httpd.objects[object_type] = data
    except:
        traceback.print_exc()
    to_exit.set()
