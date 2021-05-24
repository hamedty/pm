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

    async def script(self):
        robot_1 = ALL_NODES_DICT['Robot 1']
        station_1 = ALL_NODES_DICT['Station 1']
        rail = ALL_NODES_DICT['Rail']

        while 'm4-main' not in station_1.get_status().get('data', {}):
            await asyncio.sleep(.01)

        while 'm1' not in robot_1.get_status().get('data', {}):
            await asyncio.sleep(.01)

        while 'm' not in rail.get_status().get('data', {}):
            await asyncio.sleep(.01)

        print(1)
        await station_1.send_command({'verb': 'home', 'axis': 3})
        print(2)

        await robot_1.send_command({'verb': 'home', 'axis': 1})
        print(3)

        await robot_1.send_command({'verb': 'home', 'axis': 0})


async def main():
    SYSTEM = System(ALL_NODES)
    webserver.create_server(SYSTEM)
    await SYSTEM.connect()  # Must be ran as a command - connect and create status loop

    task1 = asyncio.create_task(SYSTEM.loop())
    task2 = asyncio.create_task(SYSTEM.script())
    await task1
    await task2

if __name__ == '__main__':
    asyncio.run(main())
