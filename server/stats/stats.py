from multiprocessing import Lock
import asyncio
import datetime


def use_lock(f):
    def wrapper(*args):
        self = args[0]
        self.lock.acquire()
        try:
            f(*args)
        finally:
            self.lock.release()
    return wrapper


def merge_dicts(active, reference):
    for key in reference:
        if type(active.get(key)) == type(reference.get(key)):
            if isinstance(active.get(key), dict):
                merge_dicts(active[key], reference[key])
        else:
            active[key] = reference[key]
    for key in list(active.keys()):
        if key not in reference:
            del active[key]


STRUCTURE = {
    'active_batch_no': 'ING0021',
    'counter': 1819,
    'counter_since': datetime.datetime.now().timestamp(),
    'speed': 2315,
    'speed_since': datetime.datetime.now().timestamp(),
}


class Stats(object):
    def __init__(self, redis):
        self.redis = redis
        self.lock = Lock()
        self.load()
        asyncio.create_task(self.background_task())

    def load(self):
        self.data = self.redis.root.stats
        self.data._setup()
        self.data = self.data._wrapped
        merge_dicts(self.data, STRUCTURE)

    async def background_task(self):
        while True:
            await asyncio.sleep(.5)
            try:
                self.redis.root.stats = self.data
            except:
                print('writing to redis failed')

    @use_lock
    def add_success(self):
        self.data['counter'] += 1

    @use_lock
    def reset_counter(self):
        self.data['counter'] = 0
        self.data['counter_since'] = datetime.datetime.now().timestamp()
