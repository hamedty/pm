import os
import json
import time
import asyncio

import tornado.ioloop
import tornado.web
import tornado.websocket
try:
    from . import annotation
except:
    annotation = None
PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH_DIR = os.path.join(PATH, 'static')
STATIC2_PATH_DIR = os.path.join(PATH, 'static2')


class Index(tornado.web.RequestHandler):
    def get(self):
        filename = os.path.join(STATIC_PATH_DIR, 'html/index.html')
        with open(filename) as f:
            content = f.read()
        self.finish(content)


class Index2(tornado.web.RequestHandler):
    def get(self):
        filename = os.path.join(STATIC2_PATH_DIR, 'html/index.html')
        with open(filename) as f:
            content = f.read()
        self.finish(content)


class Annotation(tornado.web.RequestHandler):
    def get(self):
        filename = os.path.join(STATIC_PATH_DIR, 'html/annotation.html')
        with open(filename) as f:
            content = f.read()
        self.finish(content)


class AnnotationApi(tornado.web.RequestHandler):
    def get(self):
        component = self.get_arguments("component")[0]
        station = self.get_arguments("station")[0]
        res = annotation.get(component, station)
        self.write(res)

    def post(self):
        component = self.get_arguments("component")[0]
        station = self.get_arguments("station")[0]
        data = self.request.body
        res = annotation.post(component, station, data)
        self.write(res)


class WebSocket(tornado.websocket.WebSocketHandler):
    async def open(self):
        SYSTEM.register_ws(self)

    def on_message(self, message):
        asyncio.create_task(SYSTEM.message_from_ws(json.loads(message)))

    def on_close(self):
        SYSTEM.deregister_ws(self)


class WebSocket_Mock(tornado.websocket.WebSocketHandler):
    import datetime
    data = {
        'v2': {
            'status': {
                'main_script': None,  # 'positioning' / 'feed16' / 'empty_rail' / 'main'
                # 'play' / 'pause'
            },
            'recipe': {
                'name': 'Basalin',
                'feed_open': False,
            },
            'errors': [
                {'location_name': 'Station 1', 'message': 'استیشن را خالی کنید - تنظیم هولدر',
                    'type': 'error', 'uid': '123', 'clearing': False},
                {'location_name': 'Station 3', 'message': 'استیشن را خالی کنید - تنظیم هولدر',
                    'type': 'error', 'uid': '123', 'clearing': True},
                {'location_name': 'Feeder', 'message': 'هولدر نیومده',
                    'type': 'warning', 'uid': '456'},
            ],
            'stats': {
                'active_batch_no': 'ING0021',
                'counter': 1819,
                'counter_since': (datetime.datetime.now() - datetime.timedelta(hours=2, minutes=30, days=2)).timestamp(),
                'speed': 2315,
                'speed_since': (datetime.datetime.now() - datetime.timedelta(minutes=10)).timestamp()
            },
        },
    }

    async def open(self):
        while True:
            message = self.data
            message = json.dumps(message)
            try:
                self.write_message(message)
                await asyncio.sleep(.5)
            except:
                print('Web socket connection closed!')
                return

    def on_message(self, message):
        message = json.loads(message)
        print(message)


def create_server(system=None, mock_data=False):
    global SYSTEM
    SYSTEM = system
    old_app = [
        (r"/", Index),
        (r"/ws", WebSocket_Mock if mock_data else WebSocket),
        (r'/static/(.*)', tornado.web.StaticFileHandler,
         {'path': STATIC_PATH_DIR}),
    ]

    new_hmi_app = [
        (r"/index2", Index2),
        (r'/static2/(.*)', tornado.web.StaticFileHandler,
         {'path': STATIC2_PATH_DIR}),
    ]
    app = old_app + new_hmi_app
    if annotation is not None:
        annotation_app = [
            (r"/annotation", Annotation),
            (r"/annotation/api", AnnotationApi),
            (r'/dataset/(.*)', tornado.web.StaticFileHandler,
             {'path': annotation.DATASET_PATH})
        ]
        app += annotation_app
    app = tornado.web.Application(app, debug=True)
    app.listen(8080)


def test_server(system=None):
    create_server(mock_data=True)
    tornado.ioloop.IOLoop.current().start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    test_server()
