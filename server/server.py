import SimpleHTTPServer
import SocketServer


class KcaaHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_HEAD(self):
        # Note: HTTP request handlers are not new-style classes.
        # super() cannot be used.
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_HEAD(self)

    def do_GET(self):
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


def setup(args):
    httpd = SocketServer.TCPServer(('', args.server_port),
                                   KcaaHTTPRequestHandler)
    _, port = httpd.server_address
    root_url = 'http://127.0.0.1:{}/web/'.format(port)
    print 'KCAA server ready at {}'.format(root_url)
    return httpd, root_url
