import os
import json
import time
import asyncio

import tornado.ioloop
import tornado.web
import tornado.websocket

PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_PATH_DIR = os.path.join(PATH, 'static')


class Index(tornado.web.RequestHandler):
    def get(self):
        filename = os.path.join(STATIC_PATH_DIR, 'html/index.html')
        with open(filename) as f:
            content = f.read()
        self.finish(content)


class WebSocket(tornado.websocket.WebSocketHandler):
    async def open(self):
        SYSTEM.register_ws(self)

    def on_message(self, message):
        asyncio.create_task(SYSTEM.message_from_ws(json.loads(message)))

    def on_close(self):
        SYSTEM.deregister_ws(self)


def create_server(system=None):
    global SYSTEM
    SYSTEM = system

    app = tornado.web.Application([
        (r"/", Index),
        (r"/ws", WebSocket),
        (r'/static/(.*)', tornado.web.StaticFileHandler,
         {'path': STATIC_PATH_DIR})
    ], debug=True)
    app.listen(8888)
