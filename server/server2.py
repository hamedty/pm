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


class System(object):
    def __init__(self, nodes):
        self.nodes = nodes
        self._ws = []

    async def connect(self):
        for node in self.nodes:
            res = await node.connect()
            if res:
                await node.send_command_config_arduino()
                await node.send_command_create_camera()
                asyncio.create_task(node.loop())

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
    # task2 = asyncio.create_task(SYSTEM.valves())
    await task1
    await task2

asyncio.run(main())
