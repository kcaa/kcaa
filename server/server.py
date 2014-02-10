import SimpleHTTPServer
import SocketServer


class KcaaHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    CLIENT_PREFIX = '/client/'

    def do_HEAD(self):
        # Note: HTTP request handlers are not new-style classes.
        # super() cannot be used.
        if self.rewrite_to_client_path():
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_HEAD(self)

    def do_GET(self):
        if self.rewrite_to_client_path():
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def rewrite_to_client_path(self):
        if self.path.startswith(KcaaHTTPRequestHandler.CLIENT_PREFIX):
            self.path = '/' + self.path[len(
                KcaaHTTPRequestHandler.CLIENT_PREFIX):]
            return True
        else:
            return False


def setup(args):
    httpd = SocketServer.TCPServer(('', args.server_port),
                                   KcaaHTTPRequestHandler)
    _, port = httpd.server_address
    root_url = 'http://127.0.0.1:{}/client/'.format(port)
    print 'KCAA server ready at {}'.format(root_url)
    return httpd, root_url
