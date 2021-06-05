import time
import os
import sys
import json
import traceback
from node import ALL_NODES, ALL_NODES_DICT
import asyncio

PATH = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.dirname(PATH)
sys.path.insert(0, PARENT_PATH)

import webserver.main as webserver  # nopep8
import scripts


class System(object):
    def __init__(self, nodes):
        self.nodes = nodes
        self._ws = []

    async def connect(self):
        for node in self.nodes:
            asyncio.create_task(self.setup_node(node))

    async def setup_node(self, node):
        asyncio.create_task(node.loop())
        res = await node.connect()
        if res:
            await node.send_command_config_arduino()
            await node.send_command_create_camera()

    def register_ws(self, ws):
        self.send_architecture(ws)
        self._ws.append(ws)

    def deregister_ws(self, ws):
        self._ws.remove(ws)

    async def message_from_ws(self, ws, message_in):
        response = await asyncio.gather(*[ALL_NODES_DICT[node_name].send_command_scenario(message_in['form']) for node_name in message_in['selected_nodes']], return_exceptions=True)
        message_out = {'type': 'response', 'payload': response}
        ws.write_message(json.dumps(message_out))

    def send_architecture(self, ws):
        message = [{
            'type': n.type,
            'name': n.name,
            'actions': n.get_actions(),
        } for n in self.nodes]
        message = {'type': 'architecture', 'payload': message}
        ws.write_message(json.dumps(message))

    async def loop(self):
        while True:
            message = [n.get_status() for n in self.nodes]
            message = {'type': 'status_update', 'payload': message}
            message = json.dumps(message)
            for ws in self._ws:
                ws.write_message(message)
            await asyncio.sleep(.1)

    async def script_wrapper(self, func):
        try:
            await func(self, ALL_NODES_DICT)
        except:
            print(traceback.format_exc())


async def main():
    SYSTEM = System(ALL_NODES)
    webserver.create_server(SYSTEM)
    await SYSTEM.connect()  # Must be ran as a command - connect and create status loop

    task1 = asyncio.create_task(SYSTEM.loop())

    # task2 = asyncio.create_task(SYSTEM.script_wrapper(scripts.main))
    # await task2
    await task1

if __name__ == '__main__':
    asyncio.run(main())
