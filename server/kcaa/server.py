import SimpleHTTPServer
import SocketServer
import json
import logging
import os
import traceback
import urlparse

import controller
import logenv


DEPLOYED_PACKAGE = 'build/web'
DEVELOPMENT_PACKAGE = 'web'


logenv.setup_logger()
logger = logging.getLogger('kcaa.server')


class KCAAHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    GET_OBJECTS = '/get_objects'
    GET_NEW_OBJECTS = '/get_new_objects'
    GET_OBJECT = '/get_object'
    CLICK = '/click'
    RELOAD_KCSAPI = '/reload_kcsapi'
    RELOAD_MANIPULATORS = '/reload_manipulators'
    MANIPULATE = '/manipulate'
    SET_AUTO_MANIPULATOR_SCHEDULES = '/set_auto_manipulator_schedules'
    TAKE_SCREENSHOT = '/take_screenshot'
    CLIENT_PREFIX = '/client/'

    def do_HEAD(self):
        self.dispatch()

    def do_GET(self):
        self.dispatch()

    def log_message(self, format, *args):
        # Kill verbose HTTP logging.
        pass

    def dispatch(self):
        o = urlparse.urlparse(self.path)
        if o.path == KCAAHTTPRequestHandler.GET_OBJECTS:
            self.handle_get_objects(o)
        elif o.path == KCAAHTTPRequestHandler.GET_NEW_OBJECTS:
            self.handle_get_new_objects(o)
        elif o.path == KCAAHTTPRequestHandler.GET_OBJECT:
            self.handle_get_object(o)
        elif o.path == KCAAHTTPRequestHandler.CLICK:
            self.handle_click(o)
        elif o.path == KCAAHTTPRequestHandler.RELOAD_KCSAPI:
            self.handle_reload_kcsapi(o)
        elif o.path == KCAAHTTPRequestHandler.RELOAD_MANIPULATORS:
            self.handle_reload_manipulators(o)
        elif o.path == KCAAHTTPRequestHandler.MANIPULATE:
            self.handle_manipulate(o)
        elif o.path == KCAAHTTPRequestHandler.SET_AUTO_MANIPULATOR_SCHEDULES:
            self.handle_set_auto_manipulator_schedules(o)
        elif o.path == KCAAHTTPRequestHandler.TAKE_SCREENSHOT:
            self.handle_take_screenshot(o)
        elif o.path.startswith(KCAAHTTPRequestHandler.CLIENT_PREFIX):
            self.handle_client(o)
        else:
            self.send_error(404, 'Unknown handler: {}'.format(self.path))

    def handle_get_objects(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/json; charset=UTF-8')
        self.end_headers()
        self.wfile.write(json.dumps(sorted(list(
            self.server.objects.iterkeys()))))

    def handle_get_new_objects(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/json; charset=UTF-8')
        self.end_headers()
        self.wfile.write(json.dumps(sorted(list(self.server.new_objects))))

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
            self.server.new_objects.discard(object_type)
            self.send_response(200)
            self.send_header('Content-Type', 'text/json; charset=UTF-8')
            self.end_headers()
            self.wfile.write(data)
        except KeyError:
            self.send_error(404)

    def handle_click(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        queries = urlparse.parse_qs(o.query)
        try:
            x = int(queries['x'][0])
            y = int(queries['y'][0])
        except KeyError:
            self.send_error(400, 'Missing parameter: x or y')
            return
        self.server.controller_conn.send((controller.COMMAND_CLICK, (x, y)))
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write('success')

    def handle_reload_kcsapi(self, o):
        self.server.controller_conn.send(
            (controller.COMMAND_RELOAD_KCSAPI, None))
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write('success')

    def handle_reload_manipulators(self, o):
        self.server.controller_conn.send(
            (controller.COMMAND_RELOAD_MANIPULATORS, None))
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write('success')

    def handle_manipulate(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        queries = urlparse.parse_qs(o.query)
        try:
            command_type = queries['type'][0]
            del queries['type']
        except KeyError:
            self.send_error(400, 'Missing parameter: type')
            return
        command_args = {}
        for key, values in queries.iteritems():
            if len(values) == 1:
                command_args[key] = values[0]
            else:
                command_args[key] = values
        self.server.controller_conn.send((controller.COMMAND_MANIPULATE,
                                          (command_type, command_args)))
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write('success')

    def handle_set_auto_manipulator_schedules(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        queries = urlparse.parse_qs(o.query)
        try:
            enabled = queries['enabled'][0] == 'true'
            schedule = queries['schedule'][0]
        except KeyError:
            self.send_error(400, 'Missing parameter: enabled or schedule')
            return
        schedule_fragments = [map(lambda v: int(v), fragment.split(':'))
                              for fragment in schedule.split(';')]
        self.server.controller_conn.send(
            (controller.COMMAND_SET_AUTO_MANIPULATOR_SCHEDULES,
             (enabled, schedule_fragments)))
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write('success')

    def handle_take_screenshot(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        queries = urlparse.parse_qs(o.query)
        format = queries.get('format', ['jpeg'])[0]
        quality = int(queries.get('quality', [50])[0])
        width = int(queries.get('width', [0])[0])
        height = int(queries.get('height', [0])[0])
        self.server.controller_conn.send(
            (controller.COMMAND_TAKE_SCREENSHOT,
             (format, quality, width, height)))
        self.send_response(200)
        self.send_header('Content-Type', 'image/png')
        self.end_headers()
        self.wfile.write(self.server.controller_conn.recv())

    def handle_client(self, o):
        self.path = '/' + o.path[len(KCAAHTTPRequestHandler.CLIENT_PREFIX):]
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
        logger.info(
            'Deployed package found. Using {}.'.format(DEPLOYED_PACKAGE))
        os.chdir(DEPLOYED_PACKAGE)
    elif os.path.isdir(DEVELOPMENT_PACKAGE):
        logger.info(
            'Development package found. Using {}.'.format(DEVELOPMENT_PACKAGE))
        os.chdir(DEVELOPMENT_PACKAGE)
    else:
        raise IOError('No client package directories found under {}.'.format(
            client_dir))


def setup(args):
    move_to_client_dir()
    httpd = SocketServer.TCPServer(('', args.server_port),
                                   KCAAHTTPRequestHandler,
                                   bind_and_activate=False)

    def handle_error(request, client_address):
        # Kill verbose exception logging, especially Error 32: Broken pipe.
        # This is a normal exception when the client resets the connection.
        logger.info(
            'Socket error happened while handling a request from {}'
            .format(client_address))

    httpd.handle_error = handle_error

    # If the port number is specified, allow it to be reused.
    if args.server_port != 0:
        httpd.allow_reuse_address = True
    httpd.server_bind()
    httpd.server_activate()
    _, port = httpd.server_address
    root_url = ('http://localhost:{}/client/?interval={}&screen={}&debug={}'.
                format(port, args.frontend_update_interval,
                       'true' if args.show_kancolle_screen else 'false',
                       'true' if args.debug else 'false'))
    logger.info('KCAA client ready at {}'.format(root_url))
    return httpd, root_url


def handle_server(args, to_exit, controller_conn, object_queue):
    httpd = None
    try:
        httpd, root_url = setup(args)
        httpd.new_objects = set()
        httpd.objects = {}
        httpd.controller_conn = controller_conn
        controller_conn.send(root_url)
        httpd.timeout = args.backend_update_interval
        while True:
            httpd.handle_request()
            if to_exit.wait(0.0):
                logger.info('Server got an exit signal. Shutting down.')
                break
            while not object_queue.empty():
                object_type, data = object_queue.get()
                httpd.new_objects.add(object_type)
                httpd.objects[object_type] = data
    except (KeyboardInterrupt, SystemExit):
        logger.info('SIGINT received in the server process. Exiting...')
    except:
        traceback.print_exc()
    to_exit.set()
    if httpd:
        httpd.server_close()
