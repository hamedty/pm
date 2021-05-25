import subprocess
import asyncio
import json
import traceback
import os
import time

import string
import uuid
import random


def generate_random_string():
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(random.choices(alphabet, k=8))


class Node(object):
    def __init__(self, name, ip):
        self.set_status(message='node instance creating')
        self.name = name
        self.ip = ip
        self.ip_short = int(self.ip.split('.')[-1])
        self._socket_reader = None
        self.actions = []
        self.set_status(message='node instance created')
        self.lock = None

    async def ping(self):
        command = 'ping -c 1 -W 0.5'.split()
        command.append(self.ip)
        while subprocess.call(command, stdout=subprocess.PIPE) != 0:
            await asyncio.sleep(.5)
        return True

    async def scp_to(self, path_src, path_dst):
        command = 'scp -r %s pi@%s:%s' % (path_src, self.ip, path_dst)
        command = command.split()
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

    async def connect(self):
        while not self._socket_reader:
            try:
                reader, writer = await asyncio.open_connection(self.ip, 2000)
            except:
                await asyncio.sleep(.5)
                print('retrying to connect to', self.ip)
                continue
            self._socket_reader = reader
            self._socket_writer = writer
            self.set_status(message='socket connected')

        await self.send_command({'verb': 'create_arduino'})
        return True

    async def send_command_scenario(self, command):
        if command['verb'] == 'dump_frame':
            await self.send_command(command)
            await self.scp_from('~/data/dosing.png', './dump/dosing.png')
            await self.scp_from('~/data/holder.png', './dump/holder.png')
        elif command['verb'] == 'dump_training_holder':
            random_string = generate_random_string()
            await self.send_command({'verb': 'set_valves', 'valves': [0, 1]}, assert_success=True)
            await asyncio.sleep(1)
            command['folder_name'] = random_string
            command['step_per_rev'] = 32 * 200
            await self.send_command(command, assert_success=True)

            folder_name_src = '~/data/%s' % random_string
            folder_name_dst = '../dataset/holder_%02d_%s' % (
                self.ip_short, random_string)

            await self.send_command({'verb': 'set_valves', 'valves': [0, 0]}, assert_success=True)
            await self.scp_from(folder_name_src, folder_name_dst)

        elif command['verb'] == 'dump_training_dosing':
            random_string = generate_random_string()
            await self.send_command({'verb': 'set_valves', 'valves': [1]}, assert_success=True)
            await asyncio.sleep(1)
            command['folder_name'] = random_string
            command['step_per_rev'] = 32 * 200
            await self.send_command(command, assert_success=True)

            folder_name_src = '~/data/%s' % random_string
            folder_name_dst = '../dataset/dosing_%02d_%s' % (
                self.ip_short, random_string)

            await self.send_command({'verb': 'set_valves', 'valves': [0]}, assert_success=True)
            await self.scp_from(folder_name_src, folder_name_dst)
        elif command['verb'] == 'dance':
            value = int(command.get('value', 1))
            command = {
                'verb': 'move_motors',
                'moves': [
                    [],
                    [],
                    [64 * value + command.get('extra_m3', 0), 99, 0],
                    [-11 * value, 576, 1],
                ]
            }
            await self.send_command(command)

        else:
            await self.send_command(command)

    async def send_command(self, command, assert_success=False):
        command_str = json.dumps(command) + '\n'
        command_str = command_str.encode()
        if self.lock is None:
            self.lock = asyncio.Lock()
        async with self.lock:
            self._socket_writer.write(command_str)
            line = await self._socket_reader.readline()

        try:
            line = json.loads(line)
            if assert_success:
                assert line['success']
            return line['success'], line
        except:
            if assert_success:
                raise
            trace = traceback.format_exc()
            return False, trace

    async def loop(self):
        while True:
            last_status_time = self._status['time']
            current_time = time.time()
            timeout = 0.5
            if current_time - last_status_time > timeout:
                if not self._socket_reader:
                    await asyncio.sleep(timeout)
                    continue
                success, data = await self.send_command({'verb': 'get_status'})
                if success:
                    self.set_status(**data['status'])
                    continue
                self.set_status(message='get status failed', data=data)
                continue

            await asyncio.sleep(timeout - (current_time - last_status_time))

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

    async def send_command_create_camera(self):
        return

    def set_status(self, **kwargs):
        self._status = dict(**kwargs, time=time.time())

    def get_status(self):
        data = {'connected': bool(self._socket_reader), 'age': 0}

        if data['connected']:
            data.update(self._status)
            data['age'] = time.time() - data['time']
            del data['time']

        return data

    def get_actions(self):
        return [
            {'verb': 'connect', 'params': None},
            {'verb': 'firmware_update', 'params': None},
            {'verb': 'home_m1', 'params': None},
            {'verb': 'home_m2', 'params': None},
            {'verb': 'home_m4', 'params': None},
            {'verb': 'toggle_valve', 'params': 'int'},
            {'verb': 'toggle_valve', 'params': 'int'},

        ]
