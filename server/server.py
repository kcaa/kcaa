import SimpleHTTPServer
import SocketServer
import urllib2
import urlparse


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
        proxy_controller = self.server.proxy_controller
        proxy_port = self.server.proxy_port
        get_har = 'http://{}/proxy/{}/har'.format(proxy_controller, proxy_port)
        try:
            data = urllib2.urlopen(get_har)
        except urllib2.URLError as e:
            self.send_error(501, e)
            return
        self.send_response(data.getcode())
        self.send_header('Content-Type', 'text/json')
        self.end_headers()
        self.wfile.write(data.read())

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


def setup(args):
    httpd = SocketServer.TCPServer(('', args.server_port),
                                   KcaaHTTPRequestHandler)
    httpd.proxy_controller = args.proxy_controller
    httpd.proxy_port = args.proxy.partition(':')[2]
    _, port = httpd.server_address
    # Don't use query (something like ?key=value). Kancolle widget detects it
    # from referer and rejects to respond.
    root_url = 'http://localhost:{}/client/'.format(port)
    print 'KCAA server ready at {}'.format(root_url)
    return httpd, root_url
