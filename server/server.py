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

    async def main_script(self):
        D_STANDBY = 40000
        await asyncio.sleep(1)

        robot_1 = ALL_NODES_DICT['Robot 1']
        stations = [ALL_NODES_DICT['Station %d' % (i + 1)] for i in range(5)]
        rail = ALL_NODES_DICT['Rail']
        all_nodes = stations + [robot_1, rail]
        for node in all_nodes:
            while not node.ready_for_command():
                await asyncio.sleep(.01)

        # print('Home Everything')
        # print('Home Everything - 1- robot')
        await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10}, assert_success=True)
        # await robot_1.send_command({'verb': 'home', 'axis': 1}, assert_success=True)
        # await robot_1.send_command({'verb': 'home', 'axis': 0}, assert_success=True)
        #
        # print('Home Everything - 2- stations and rail together')
        # tasks = []
        # for station in stations:
        #     tasks.append(station.send_command(
        #         {'verb': 'set_valves', 'valves': [0] * 5}, assert_success=True))
        #     tasks.append(station.send_command(
        #         {'verb': 'home', 'axis': 3}, assert_success=True))
        #
        # tasks.append(rail.send_command(
        #     {'verb': 'home', 'axis': 0}, assert_success=True))
        #
        # await asyncio.gather(*tasks)
        # await rail.goto(D_STANDBY)

        while True:
            await rail.is_homed()

            print('Take robot to starting point')
            X = 4000
            Y = 8250
            await robot_1.goto(y=Y)
            await robot_1.goto(x=X)

            input('continue?')
            print('lets go grab input')
            X = 22750
            Y1 = 0
            Y2 = 6250
            await robot_1.goto(x=X)
            await robot_1.goto(y=Y1)

            await robot_1.send_command(
                {'verb': 'set_valves', 'valves': [1] * 10})
            await asyncio.sleep(1)

            await robot_1.goto(y=Y2)
            print('put input into station')
            X = 30000
            Y1 = 1600
            Y2 = 675
            Y3 = Y1
            # await asyncio.gather(
            #     robot_1.goto(x=X),
            #     station_1.send_command(
            #         {'verb': 'set_valves', 'valves': [0, 0, 0, 1]}),
            # )
            await robot_1.goto(x=X)
            await robot_1.goto(y=Y1)
            await robot_1.send_command(
                {'verb': 'set_valves', 'valves': [0] * 10})
            await asyncio.sleep(.5)

            continue
            print('press holder in')

            await robot_1.send_command(
                {'verb': 'set_valves', 'valves': [0, 0, 0, 0, 0, 1]})
            await robot_1.goto(y=Y2)
            await asyncio.sleep(.2)
            await robot_1.goto(y=Y3)

            print('Move back for station to work')
            X = 47000 / 2
            move_robot_back = asyncio.create_task(robot_1.goto(x=X))
            align_holder = asyncio.create_task(station_1.send_command(
                {'verb': 'align', 'component': 'holder'}))
            await move_robot_back

            print('prepare dosing')
            H_ALIGNING = 21500
            H_PUSH = 23000
            H_PUSH_BACK = H_PUSH - 500
            H_GRIPP = 23700

            await station_1.send_command({'verb': 'move_motors', 'moves': [
                [], [], [], [H_ALIGNING, 150, 1, 1]]})
            await station_1.send_command({'verb': 'align', 'component': 'dosing'})
            await station_1.send_command({'verb': 'set_valves', 'valves': [0, None, 0, 0]})
            await asyncio.sleep(.3)
            await station_1.send_command({'verb': 'set_valves', 'valves': [1]})
            await asyncio.sleep(.2)
            await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_PUSH, 150, 1, 1]]})
            await asyncio.sleep(.2)
            await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_PUSH_BACK, 150, 1, 1]]})
            await station_1.send_command({'verb': 'set_valves', 'valves': [0, None, 0, 1]})
            await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_GRIPP, 150, 1, 1]]})
            await asyncio.sleep(.1)
            await station_1.send_command({'verb': 'set_valves', 'valves': [1, None, 0, 1]})
            await asyncio.sleep(.3)
            await station_1.send_command_scenario({'verb': 'dance', 'value': 100})
            await station_1.send_command({'verb': 'set_valves', 'valves': [0, 0, 0, 0, 1]})
            await align_holder

            print('press')
            H_DELIVER = 4000
            X_DELIVER = 59800 / 2
            Y_DELIVER = 16700 / 2
            H_CLEAR = 2000
            await asyncio.sleep(.1)
            await station_1.send_command({'verb': 'set_valves', 'valves': [0, 0, 1]})
            await asyncio.sleep(1)
            await station_1.send_command({'verb': 'set_valves', 'valves': [0, 0, 0]})
            await asyncio.sleep(.2)
            await station_1.send_command({'verb': 'set_valves', 'valves': [1, 0, 0, 0, 0]})
            await asyncio.sleep(.2)
            await station_1.send_command_scenario({'verb': 'dance', 'value': -100, 'extra_m3': -100})
            await asyncio.sleep(.2)
            await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_DELIVER, 150, 1, 1]]})
            await robot_1.goto(y=Y_DELIVER)
            await robot_1.goto(x=X_DELIVER)
            await robot_1.send_command({'verb': 'set_valves', 'valves': [1]})
            await asyncio.sleep(.2)
            await station_1.send_command({'verb': 'set_valves', 'valves': [0]})
            await station_1.send_command({'verb': 'move_motors', 'moves': [[], [], [], [H_CLEAR, 150, 1, 1]]})

            print('Capping')
            X_CAPPING = 8200 / 2
            Y_CAPPING_1 = 7000 / 2

            await robot_1.goto(x=X_CAPPING)
            await robot_1.goto(y=Y_CAPPING_1)
            await robot_1.send_command({'verb': 'set_valves', 'valves': [0]})

    async def main_script_wrapper(self):
        try:
            await self.main_script()
        except:
            print(traceback.format_exc())

    async def speed_test_station(self):
        try:
            node = ALL_NODES_DICT['Station 1']
            print(1)
            while 'm4-main' not in node.get_status().get('data', {}):
                await asyncio.sleep(.01)
            print(2)
            await asyncio.sleep(2)
            await node.send_command({'verb': 'home', 'axis': 3}),

            t0 = time.time()
            await node.send_command(
                ({'verb': 'move_motors', 'moves': [[], [], [], [21500, 300, 1, 1]]}))
            t1 = time.time()
            print(t1 - t0)

            await asyncio.sleep(.5)
            await node.send_command(
                ({'verb': 'move_motors', 'moves': [[], [], [], [1, 300, 1, 1]]}))
        except:
            print(traceback.format_exc())

    async def speed_test_robot(self):
        try:

            node = ALL_NODES_DICT['Robot 1']
            print(1)
            while 'm1' not in node.get_status().get('data', {}):
                await asyncio.sleep(.01)
            print(2)
            await node.send_command({'verb': 'home', 'axis': 0}),

            t0 = time.time()
            await node.send_command(
                ({'verb': 'move_motors', 'moves': [[9000, 300, 1, 1]]}))
            t1 = time.time()
            print(t1 - t0)

            await asyncio.sleep(.5)
            await node.send_command(
                ({'verb': 'move_motors', 'moves': [[1, 300, 1, 1]]}))
        except:
            print(traceback.format_exc())

    async def move_rail(self):
        X_PARK = 40000
        X1 = 20000
        X2 = 60000  # 24000
        DELAY_MOTOR = .001
        DELAY_FIXED_JACK = 0.7
        DELAY_MOVING_JACK = 0.7

        try:
            node = ALL_NODES_DICT['Rail']
            print(1)
            while 'm' not in node.get_status().get('data', {}):
                await asyncio.sleep(.01)

            await node.send_command({'verb': 'set_valves', 'valves': [0, 0]})
            await asyncio.sleep(DELAY_FIXED_JACK)
            # await node.send_command({'verb': 'home', 'axis': 0}),
            await node.send_command(({'verb': 'move_motors', 'moves': [[40000, 300, 1, 1]]}))
            await asyncio.sleep(DELAY_MOTOR)

            while True:
                for i in range(20):
                    await node.send_command(({'verb': 'move_motors', 'moves': [[X1, 300, 1, 1]]}))
                    await asyncio.sleep(DELAY_MOTOR)

                    await node.send_command({'verb': 'set_valves', 'valves': [0, 1]})
                    await asyncio.sleep(DELAY_MOVING_JACK)

                    await node.send_command({'verb': 'set_valves', 'valves': [1, 1]})
                    await asyncio.sleep(DELAY_FIXED_JACK)

                    await node.send_command(({'verb': 'move_motors', 'moves': [[X2, 300, 1, 1]]}))
                    await asyncio.sleep(DELAY_MOTOR)

                    await node.send_command({'verb': 'set_valves', 'valves': [0, 1]})
                    await asyncio.sleep(DELAY_FIXED_JACK)

                    await node.send_command({'verb': 'set_valves', 'valves': [0, 0]})
                    await asyncio.sleep(DELAY_MOVING_JACK)

                    await node.send_command(({'verb': 'move_motors', 'moves': [[X_PARK, 300, 1, 1]]}))
                    await asyncio.sleep(DELAY_MOTOR)
                input('repeat?')

            # t0 = time.time()
            # t1 = time.time()
            # print(t1 - t0)
        except:
            print(traceback.format_exc())


async def main():
    SYSTEM = System(ALL_NODES)
    webserver.create_server(SYSTEM)
    await SYSTEM.connect()  # Must be ran as a command - connect and create status loop

    task1 = asyncio.create_task(SYSTEM.loop())

    # task2 = asyncio.create_task(SYSTEM.main_script_wrapper())
    # await task2
    await task1

if __name__ == '__main__':
    asyncio.run(main())
