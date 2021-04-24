import time
import subprocess
import asyncio
import json
import traceback

CHECK_GREEN = '\033[92m✓\033[0m'
CROSS_RED = '\033[91m✖\033[0m'


class Node(object):
    def __init__(self, ip):
        self.ip = ip
        self._socket_reader = None

    async def ping(self):
        command = 'ping -c 1 -W 0.5'.split()
        command.append(self.ip)
        while subprocess.call(command, stdout=subprocess.PIPE) != 0:
            await asyncio.sleep(.5)
        return True

    async def scp(self, path_src, path_dst):
        command = 'scp -r %s pi@%s:%s' % (path_src, self.ip, path_dst)
        command = command.split()
        while subprocess.call(command, stdout=subprocess.PIPE) != 0:
            await asyncio.sleep(.5)
        return True

    async def connect(self):
        if not self._socket_reader:
            reader, writer = await asyncio.open_connection(self.ip, 2000)
            self._socket_reader = reader
            self._socket_writer = writer
        return True

    async def send_command(self, command):
        command = json.dumps(command) + '\n'
        self._socket_writer.write(command.encode())
        # await self._socket_writer.drain()
        line = await self._socket_reader.readline()
        try:
            line = json.loads(line)
            print('response', line)
            return line['success']
        except:
            traceback.print_exc()
            return False

    async def send_command_reset_arduino(self):
        command = {
            'verb': 'reset_arduino',
            'pin': self.arduino_reset_pin,
        }
        return await self.send_command(command)

    async def send_command_config_arduino(self):
        command = {
            'verb': 'config_arduino',
            'hw_config': self.hw_config,
        }
        return await self.send_command(command)

    async def send_command_set_valves(self, valves):
        command = {
            'verb': 'set_valves',
            'valves': valves,
        }
        return await self.send_command(command)


class Station(Node):
    arduino_reset_pin = 21
    hw_config = {
        'valves': [8, 7, 6, 5, 4, 3],
        'motors': [
            {
                'pin_pulse': 43,
                'pin_dir': 42,
                'pin_microstep_0': 46,
                'pin_microstep_1': 45,
                'pin_microstep_2': 44,
                'microstep': 32,
            },
            {
                'pin_pulse': 25,
                'pin_dir': 23,
                'pin_microstep_0': 31,
                'pin_microstep_1': 29,
                'pin_microstep_2': 27,
                'microstep': 32,
            },
            {
                'pin_pulse': 48,
                'pin_dir': 47,
                'pin_microstep_0': 51,
                'pin_microstep_1': 50,
                'pin_microstep_2': 49,
                'microstep': 32,
            },
            {
                'pin_pulse': 35,
                'pin_dir': 33,
                'pin_limit_n': 28,
                'microstep': 2500,
            },
        ]
    }
    pass


class Robot(Node):
    arduino_reset_pin = 2
    valves = [15, 16]
    hw_config = {
        'valves': [37, 39],
        'motors': [
            {
                'pin_pulse': 12,
                'pin_dir': 11,
                # 'pin_limit_n': 15,
                # 'pin_limit_p': 16,
                'microstep': 2500,
            },
            {
                'pin_pulse': 9,
                'pin_dir': 8,
                'pin_limit_n': 14,
                'pin_limit_p': 0,
                'microstep': 2500,
            },
        ]
    }


class Rail(Robot):
    pass


STATIONS = [
    # First Five
    None,
    None,
    Station('192.168.44.52'),  # 23
    None,
    None,

    # Second Five
    # Station('192.168.44.26'),
    # Station('192.168.44.27'),
    # Station('192.168.44.28'),
    # Station('192.168.44.29'),
    # Station('192.168.44.30'),
]
ROBOTS = [
    Robot('192.168.44.51'),  # Robot('192.168.44.11'),
    None,  # Robot('192.168.44.12'),
]

RAIL = [
    # Rail('192.168.44.10'),
]
ALL_NODES = STATIONS + ROBOTS + RAIL
ALL_NODES = [node for node in ALL_NODES if node]
ALL_NODES = [Robot('192.168.44.51')]
# ALL_NODES = [Station('127.0.0.1')]
N = len(ALL_NODES)


async def call_all_wrapper(func, timeout=None):
    result = await asyncio.gather(*[asyncio.wait_for(func(node), timeout=timeout) for node in ALL_NODES], return_exceptions=True)
    for i in range(N):
        print('\t%s: ' % ALL_NODES[i].ip, end='')
        if result[i] == True:
            print(CHECK_GREEN)
        else:
            print(CROSS_RED, repr(result[i]))
    return result


async def main():
    # Ping Nodes
    print('Ping nodes ...')
    result = await call_all_wrapper(lambda x: x.ping(), timeout=5)
    assert(all(result))

    # Connect to them
    print('Connecting to nodes ...')
    result = await call_all_wrapper(lambda x: x.connect(), timeout=1)
    assert(all(result))

    # # reset arduino
    # print('reseting arduino ...')
    # result = await call_all_wrapper(lambda x: x.send_command_reset_arduino(), timeout=5)
    # assert(all(result))

    # define valves
    print('config arduino ...')
    result = await call_all_wrapper(lambda x: x.send_command_config_arduino(), timeout=2)
    assert(all(result))

    # set valves
    print('set valves ...')
    result = await call_all_wrapper(lambda x: x.send_command_set_valves([0, 1]), timeout=20)
    assert(all(result))


asyncio.run(main())
