import pymongo
import queue
import threading

client = pymongo.MongoClient()
db = client["PAM2060"]


class Mongo(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self._q = queue.Queue(maxsize=1000)

    def run(self):
        while True:
            table, data = self._q.get()
            db[table].insert_one(data)

    def write(self, table, data):
        self._q.put((table, data), block=False)
