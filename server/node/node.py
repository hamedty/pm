import subprocess
import asyncio
import json
import traceback
import os
import time
from multiprocessing import Lock


class Node(object):
    def __init__(self, name, ip):
        self.set_status(message='node instance creating')
        self.name = name
        self.ip = ip
        self._socket_reader = None
        self.lock = Lock()
        self.actions = []
        self.set_status(message='node instance created')

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
        if not self._socket_reader:
            reader, writer = await asyncio.open_connection(self.ip, 2000)
            self._socket_reader = reader
            self._socket_writer = writer
            self.set_status(message='socket connected')

        await self.send_command({'verb': 'create_arduino'})
        return True

    async def send_command(self, command):
        command = json.dumps(command) + '\n'

        self.lock.acquire()
        self._socket_writer.write(command.encode())
        line = await self._socket_reader.readline()
        self.lock.release()

        try:
            line = json.loads(line)
            print('response', line)
            return line['success'], line
        except:
            trace = traceback.format_exc()
            return False, trace

    async def loop(self):
        while True:
            last_status_time = self._status['time']
            current_time = time.time()
            timeout = 0.5
            if current_time - last_status_time > timeout:
                success, data = await self.send_command({'verb': 'get_status'})
                if success:
                    self.set_status(**data['status'])
                else:
                    self.set_status(message='get status failed', data=data)
            else:
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

    async def send_command_set_valves(self, valves):
        command = {
            'verb': 'set_valves',
            'valves': valves,
        }
        return await self.send_command(command)

    def set_status(self, **kwargs):
        self._status = dict(**kwargs, time=time.time())

    def get_status(self):
        data = {'connected': bool(self._socket_reader)}
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
