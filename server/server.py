import SimpleHTTPServer
import SocketServer
import json
import logging
import os
import urlparse


DEPLOYED_PACKAGE = 'build'
DEVELOPMENT_PACKAGE = 'web'


class KcaaHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    GETSTATE = '/getstate'
    CLIENT_PREFIX = '/client/'

    def do_HEAD(self):
        self.dispatch()

    def do_GET(self):
        self.dispatch()

    def dispatch(self):
        o = urlparse.urlparse(self.path)
        if o.path == KcaaHTTPRequestHandler.GETSTATE:
            self.handle_getstate(o)
        elif o.path.startswith(KcaaHTTPRequestHandler.CLIENT_PREFIX):
            self.handle_client(o)
        else:
            self.send_error(404, 'File not found: {}'.format(self.path))

    def handle_getstate(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/json')
        self.end_headers()
        self.wfile.write(json.dumps(self.server.state))

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
                                              'client'))
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
    logger = logging.getLogger('kcaa.server')
    # Wait until the controller reset the proxy.
    if not controller_conn.poll(3.0):
        logger.error('Controller couldn\'t reset the proxy. Shutting down.')
        to_exit.set()
        return
    assert controller_conn.recv()
    httpd, root_url = setup(args, logger)
    httpd.state = []
    controller_conn.send(root_url)
    httpd.timeout = 1.0
    while True:
        httpd.handle_request()
        if to_exit.wait(0.0):
            logger.info('Server got an exit signal. Shutting down.')
            break
        while controller_conn.poll():
            httpd.state.append(controller_conn.recv())
    to_exit.set()
