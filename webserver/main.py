import os
import json
import time

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
    def open(self):
        while True:
            response = [u"You said %d: " % time.time()]
            self.write_message(json.dumps(response))
            time.sleep(1)

    def on_message(self, message):
        return

    # def on_close(self):
    #     print("WebSocket closed")


def make_app():
    return tornado.web.Application([
        (r"/", Index),
        (r"/ws", WebSocket),
        (r'/static/(.*)', tornado.web.StaticFileHandler,
         {'path': STATIC_PATH_DIR})
    ], debug=True)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
