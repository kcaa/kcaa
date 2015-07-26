import SimpleHTTPServer
import SocketServer
import json
import logging
import os
import traceback
import urlparse

import controller
import logenv


class KCAAHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    GET_OBJECTS = '/get_objects'
    GET_NEW_OBJECTS = '/get_new_objects'
    GET_OBJECT_TYPES = '/get_object_types'
    GET_OBJECT = '/get_object'
    REQUEST_OBJECT = '/request_object'
    CLICK = '/click'
    RELOAD_KCSAPI = '/reload_kcsapi'
    RELOAD_MANIPULATORS = '/reload_manipulators'
    MANIPULATE = '/manipulate'
    SET_PREFERENCES = '/set_preferences'
    TAKE_SCREENSHOT = '/take_screenshot'
    CLIENT_PREFIX = '/client/'

    def do_HEAD(self):
        self.dispatch()

    def do_GET(self):
        self.dispatch()

    def do_POST(self):
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
        elif o.path == KCAAHTTPRequestHandler.GET_OBJECT_TYPES:
            self.handle_get_object_types(o)
        elif o.path == KCAAHTTPRequestHandler.GET_OBJECT:
            self.handle_get_object(o)
        elif o.path == KCAAHTTPRequestHandler.REQUEST_OBJECT:
            self.handle_request_object(o)
        elif o.path == KCAAHTTPRequestHandler.CLICK:
            self.handle_click(o)
        elif o.path == KCAAHTTPRequestHandler.RELOAD_KCSAPI:
            self.handle_reload_kcsapi(o)
        elif o.path == KCAAHTTPRequestHandler.RELOAD_MANIPULATORS:
            self.handle_reload_manipulators(o)
        elif o.path == KCAAHTTPRequestHandler.MANIPULATE:
            self.handle_manipulate(o)
        elif o.path == KCAAHTTPRequestHandler.SET_PREFERENCES:
            self.handle_set_preferences(o)
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
        self.wfile.write(json.dumps(self.server.objects))

    def handle_get_new_objects(self, o):
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/json; charset=UTF-8')
        self.end_headers()
        self.wfile.write(json.dumps(
            {object_type: self.server.objects[object_type]
             for object_type in self.server.new_objects}))
        self.server.new_objects.clear()

    def handle_get_object_types(self, o):
        # This is no longer required for the client, but useful for debugging.
        if self.command != 'GET':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/json; charset=UTF-8')
        self.end_headers()
        self.wfile.write(json.dumps(sorted(list(
            self.server.objects.iterkeys()))))

    def handle_get_object(self, o):
        # This is no longer required for the client, but useful for debugging.
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

    def handle_request_object(self, o):
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
        self.server.controller_conn.send((controller.COMMAND_REQUEST_OBJECT,
                                          (command_type, command_args)))
        try:
            obj = self.server.controller_conn.recv()
        except EOFError:
            self.send_error(500, 'Controller process does not respond')
            return
        if obj:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(obj)
        else:
            self.send_error(400, 'Request failed: {}'.format(command_type))

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

    def handle_set_preferences(self, o):
        if self.command != 'POST':
            self.send_error(501, 'Unknown method: {}'.format(self.command))
            return
        queries = urlparse.parse_qs(self.rfile.read(
            int(self.headers['Content-Length'])))
        try:
            preferences_string = queries['prefs'][0]
        except KeyError:
            self.send_error(400, 'Missing parameter: prefs')
            return
        self.server.controller_conn.send(
            (controller.COMMAND_SET_PREFERENCES, (preferences_string,)))
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
        try:
            screenshot = self.server.controller_conn.recv()
        except EOFError:
            self.send_error(500, 'Controller process does not respond')
            return
        self.send_response(200)
        self.send_header('Content-Type', 'image/{}'.format(format))
        self.end_headers()
        self.wfile.write(screenshot)

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


def move_to_client_dir(logger):
    # Change directory to client directory so that SimpleHTTPServer can serve
    # client resources.
    kcaa_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..',))
    os.chdir(kcaa_dir)
    # Use 'build' subdirectory when deployed, or 'web' when being developed.
    # Prefer if there is deployed directory. This is the default when released.
    packages = [
        'client_deployed/build/web',
        'client/build/web',
        'client/web',
    ]
    for package in packages:
        if os.path.isdir(package):
            logger.info('Package found at {}'.format(package))
            os.chdir(package)
            return
    else:
        raise IOError('No client package directories found under {}.'.format(
            kcaa_dir))


def setup(args, logger):
    move_to_client_dir(logger)
    httpd = SocketServer.TCPServer(('', args.server_port),
                                   KCAAHTTPRequestHandler,
                                   bind_and_activate=False)

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
        logenv.setup_logger(args.debug, args.log_file, args.log_level,
                            args.keep_timestamped_logs)
        logger = logging.getLogger('kcaa.server')
        KCAAHTTPRequestHandler.extensions_map.update({
            '.dart': 'application/dart',
        })
        httpd, root_url = setup(args, logger)
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
                to_update, object_type, data = object_queue.get()
                if to_update:
                    httpd.new_objects.add(object_type)
                httpd.objects[object_type] = data
    except (KeyboardInterrupt, SystemExit):
        logger.info('SIGINT received in the server process. Exiting...')
    except:
        logger.error(traceback.format_exc())
    to_exit.set()
    if httpd:
        httpd.server_close()
