import datetime
import os
import sys
import uuid
import json
import traceback
import types
from node import ALL_NODES, ALL_NODES_DICT
import asyncio
import mongo

PATH = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.dirname(PATH)
sys.path.insert(0, PARENT_PATH)

import webserver.main as webserver  # nopep8
import scripts
import rpi_scripts  # for sake of reload


class System(object):
    def __init__(self, nodes):
        self.nodes = nodes
        self._ws = []
        self.system_running = asyncio.Event()
        self.system_running.set()
        self.system_stop = asyncio.Event()
        self.system_stop.clear()
        self.errors = {}
        self.errors_events = {}
        self.error_lock = asyncio.Lock()

        # mongo db access point
        self.mongo = mongo.Mongo()
        self.mongo.start()

    async def connect(self):
        for node in self.nodes:
            asyncio.create_task(self.setup_node(node))

    async def setup_node(self, node):
        res = await node.connect()
        asyncio.create_task(node.loop())
        node.boot = True

    async def register_error(self, error):
        error_id = str(uuid.uuid1())
        error_event = asyncio.Event()
        error_event.clear()
        error['time'] = datetime.datetime.now().isoformat()
        error['error_id'] = error_id
        async with self.error_lock:
            # self.system_running.clear()
            self.errors[error_id] = error
            self.errors_events[error_id] = error_event
        return error_event

    async def clear_error(self, error_id):
        async with self.error_lock:
            del self.errors[error_id]
            self.errors_events[error_id].set()
            del self.errors_events[error_id]

            # if not(self.errors):
            #     self.system_running.set()

    def register_ws(self, ws):
        self.send_architecture(ws)
        self._ws.append(ws)

    def deregister_ws(self, ws):
        self._ws.remove(ws)

    async def message_from_ws(self, ws, message_in):
        if message_in['selected_nodes']:
            response = await asyncio.gather(*[ALL_NODES_DICT[node_name].send_command_from_hmi(message_in['form']) for node_name in message_in['selected_nodes']], return_exceptions=True)
        else:
            response = self.system_command_scenario(message_in['form'])
        message_out = {'type': 'response', 'payload': response}
        print(message_out)
        ws.write_message(json.dumps(message_out))

    def send_architecture(self, ws):
        message = [{
            'type': n.type,
            'name': n.name,
        } for n in self.nodes]
        message = {
            'type': 'architecture',
            'payload': message,
            'scripts': [i for i in dir(scripts) if isinstance(getattr(scripts, i), types.FunctionType)],
        }
        ws.write_message(json.dumps(message))

    async def loop(self):
        while True:
            message = [n.get_status() for n in self.nodes]
            message = {
                'type': 'status_update',
                'nodes': message,
                'system': self._get_status(),
                'errors': self.errors,
            }
            message = json.dumps(message)
            for ws in self._ws:
                ws.write_message(message)
            await asyncio.sleep(.1)

    async def script_wrapper_always(self, func=None):
        if func is None:
            return
        await func(self, ALL_NODES)
        # while True:
        #     input('start?')
        #     try:
        #         await func(self, ALL_NODES_DICT)
        #     except:
        #         print(traceback.format_exc())

    def _get_status(self):
        status = {
            'running': self.system_running.is_set()
        }
        return status

    def system_command_scenario(self, form):
        if 'system_running' in form:
            if form['system_running']:
                self.system_running.set()
                self.system_stop.clear()
            else:
                self.system_running.clear()
        if 'system_stop' in form:
            self.system_stop.set()
        if 'clear_error' in form:
            asyncio.create_task(self.clear_error(form['clear_error']))
        if 'script' in form:
            script = getattr(scripts, form['script'])
            asyncio.create_task(self.script_wrapper_always(script))
        return {}


async def main():
    SYSTEM = System(ALL_NODES)
    webserver.create_server(SYSTEM)
    await SYSTEM.connect()  # Must be ran as a command - connect and create status loop

    task1 = asyncio.create_task(SYSTEM.loop())
    # await SYSTEM.script_wrapper_always(scripts.main)
    await task1


if __name__ == '__main__':

    asyncio.run(main())
