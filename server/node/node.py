import subprocess
import asyncio
import json
import traceback
import os
import time
import copy

import string
import uuid
import random


def generate_random_string():
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(random.choices(alphabet, k=8))


class Node(object):
    HOMMING_RETRIES = 2

    def __init__(self, name, ip, arduino_id=None):
        self.set_status(message='node instance creating')
        self.name = name
        self.ip = ip
        self.ip_short = int(self.ip.split('.')[-1])
        self.arduino_id = arduino_id
        self.hw_config = copy.deepcopy(self.hw_config_base)
        self.g2core_config = copy.deepcopy(self.g2core_config_base)

        self._socket_reader = None
        self.set_status(message='node instance created')
        self.lock = None
        self.homed = False
        self.events = {}

    async def ping(self):
        command = 'ping -c 1 -W 0.5'.split()
        command.append(self.ip)
        while subprocess.call(command, stdout=subprocess.PIPE) != 0:
            await asyncio.sleep(.5)
        return True

    async def scp_from(self, path_src, path_dst):
        path_dst, file_extension = os.path.splitext(path_dst)
        path_dst = path_dst + '_' + self.ip + file_extension
        command = 'scp -r pi@%s:%s %s' % (self.ip, path_src, path_dst)
        command = command.split()
        res = subprocess.call(command, stdout=subprocess.PIPE)
        return res == 0

    async def scp_to(self, path_src, path_dst):
        command = 'rsync -az %s pi@%s:%s' % (path_src, self.ip, path_dst)
        proc = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        assert proc.returncode == 0, proc.returncode

    async def connect(self):
        while not self._socket_reader:
            try:
                reader, writer = await asyncio.open_connection(self.ip, 2000)
                reader2, writer2 = await asyncio.open_connection(self.ip, 2000)
            except:
                await asyncio.sleep(.5)
                # print('retrying to connect to', self.ip)
                continue
            self._socket_reader = reader
            self._socket_writer = writer
            self._socket2_reader = reader2
            self._socket2_writer = writer2

            self.set_status(message='socket connected')

        await self.send_command({'verb': 'create_arduino'})
        return True

    async def send_command_raw(self, data, wait_start=[1, 3, 4], wait_completion=True):
        command = {
            'verb': 'raw',
            'data': data,
            'wait_start': wait_start,
            'wait_completion': wait_completion,
        }

        res = await self.send_command(command)
        if wait_completion:
            return self.get_status()
        else:
            return res

    async def send_command_scenario(self, command):
        if command['verb'] == 'dump_frame':
            await self.send_command(command)
            await self.scp_from('~/data/dosing.png', './dump/dosing.png')
            await self.scp_from('~/data/holder.png', './dump/holder.png')
            self.draw_debug_dump()
        elif command['verb'] == 'dump_training_holder':
            await self.set_valves([0, 1])
            await asyncio.sleep(1)

            random_string = generate_random_string()
            command['verb'] = 'dump_training'
            command['component'] = 'holder'
            command['speed'] = 10000
            command['folder_name'] = random_string

            await self.send_command(command, assert_success=True)

            folder_name_src = '~/data/%s' % random_string
            folder_name_dst = '../dataset/holder_%02d_%s' % (
                self.ip_short, random_string)

            await self.set_valves([0, 0])
            await self.scp_from(folder_name_src, folder_name_dst)

        elif command['verb'] == 'dump_training_dosing':
            if command.get('prepare'):
                await self.G1(z=self.hw_config['H_ALIGNING'], feed=10000)
            await self.set_valves([1])
            await asyncio.sleep(1)

            random_string = generate_random_string()
            command['verb'] = 'dump_training'
            command['component'] = 'dosing'
            command['speed'] = 10000
            command['folder_name'] = random_string

            await self.send_command(command, assert_success=True)

            folder_name_src = '~/data/%s' % random_string
            folder_name_dst = '../dataset/dosing_%02d_%s' % (
                self.ip_short, random_string)

            await self.set_valves([0])
            if command.get('prepare'):
                await self.G1(z=1, feed=10000)
            await self.scp_from(folder_name_src, folder_name_dst)

        elif command['verb'] == 'home':
            await self.home()
        else:
            return await self.send_command(command)

    async def send_command(self, command, assert_success=True):
        command['arduino_index'] = self.arduino_id
        command_str = json.dumps(command) + '\n'
        command_str = command_str.encode()
        if self.lock is None:
            self.lock = asyncio.Lock()
        async with self.lock:
            self._socket_writer.write(command_str)
            line = await self._socket_reader.readline()

        line = json.loads(line)
        if 'status' in line:
            self.set_status(**line['status'])
        if assert_success:
            assert line['success'], (line, self.ip, self.arduino_id)
        elif not line['success']:
            print('send command silenly failed:', line)
        return line['success'], line

    async def loop(self):
        command = {'verb': 'status_hook'}
        command['arduino_index'] = self.arduino_id
        command = json.dumps(command) + '\n'
        command = command.encode()
        self._socket2_writer.write(command)
        while True:
            line = await self._socket2_reader.readline()
            line = json.loads(line)
            self.set_status(**line)

    async def send_command_config_arduino(self):
        await self.scp_to('./rpi_scripts.py', '~/server/')
        command = {
            'verb': 'config_arduino',
            'g2core_config': self.g2core_config,
            'hw_config': self.hw_config,
        }
        await self.send_command(command)

    async def restart_arduino(self):
        command = {
            'verb': 'restart_arduino',
        }
        await self.send_command(command)
        await self.send_command_config_arduino()

    async def set_valves(self, values):
        N = min(len(self.hw_config['valves']), len(values))
        data = {}
        for i in range(1, N + 1):
            data[i] = values[i - 1]
        data = {'out': data}
        return await self.send_command_raw(json.dumps(data), wait_start=[], wait_completion=False)

    async def send_command_create_camera(self):
        return

    async def G1(self, **kwargs):
        # if not self.homed:
        #     raise
        # kwargs: x, y, z, feed
        command = {'verb': 'G1'}
        command.update(kwargs)
        return await self.send_command(command)

    def ready_for_command(self):
        return 'enc1' in self._status

    def set_status(self, **kwargs):
        self._status = kwargs
        self._status['time'] = time.time()

    def get_status(self):
        data = {'connected': bool(self._socket_reader), 'age': 0}

        if data['connected']:
            data.update(self._status)
            #data['age'] = time.time() - data['time']
            del data['time']
            del data['age']
        for event in self.events:
            data[event] = self.events[event].is_set()
        return data

    async def home(self):
        self.homed = False
        for retry in range(self.HOMMING_RETRIES):
            try:
                await self.restart_arduino()
                await asyncio.sleep(1)
                await self.home_core()
                self.homed = True
                print('%s Homed!' % self.name)
                return
            except:
                print('repeating home - homming failed')
        raise Exception('Homing Failed')

    def get_loc(self, axis):
        # axis in {'x', 'y', 'z'}
        enc_name, enc_ratio, telorance = self.hw_config['encoders']['pos' + axis]
        enc_location = self._status[enc_name] / float(enc_ratio)
        g2_location = self._status['r.pos' + axis]
        assert abs(g2_location - enc_location) < telorance
        return g2_location, enc_location, telorance

    def is_at_loc(self, **kwargs):
        # x=10, y=20, z=30
        for axis in kwargs:
            desired_location = kwargs[axis]
            g2_location, enc_location, telorance = self.get_loc(axis)
            if abs(desired_location - enc_location) > telorance:
                return False
        return True
