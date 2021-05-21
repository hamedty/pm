import time
import os
import sys
import json

from node import ALL_NODES, ALL_NODES_DICT
import asyncio

PATH = os.path.dirname(os.path.abspath(__file__))
PARENT_PATH = os.path.dirname(PATH)
sys.path.insert(0, PARENT_PATH)

import webserver.main as webserver  # nopep8

# CHECK_GREEN = '\033[92m✓\033[0m'
# CROSS_RED = '\033[91m✖\033[0m'
#
#
# async def call_all_wrapper(func, timeout=None):
#     result = await asyncio.gather(*[asyncio.wait_for(func(node), timeout=timeout) for node in ALL_NODES], return_exceptions=True)
#     for i in range(N):
#         print('\t%s: ' % ALL_NODES[i].ip, end='')
#         if result[i] == True:
#             print(CHECK_GREEN, repr(result[i]))
#         else:
#             print(CROSS_RED, repr(result[i]))
#     return result
#
# result = await call_all_wrapper(lambda x: x.ping(), timeout=5)
# assert(all(result))


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

    async def message_from_ws(self, message):
        print(message)
        for node_name in message['selected_nodes']:
            node = ALL_NODES_DICT[node_name]
            await node.send_command_scenario(message['form'])

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

    async def valves(self):
        while True:
            for i in range(10):
                for node in self.nodes[:2]:
                    valves = [0] * 10
                    valves[i] = 1
                    await node.send_command_set_valves(valves)
                await asyncio.sleep(1)


async def main():
    SYSTEM = System(ALL_NODES)
    webserver.create_server(SYSTEM)
    await SYSTEM.connect()  # Must be ran as a command - connect and create status loop

    task1 = asyncio.create_task(SYSTEM.loop())
    await task1

asyncio.run(main())
