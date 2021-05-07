import subprocess
import asyncio
import json
import traceback
import os


class Node(object):
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
        self._socket_reader = None
        self.actions = []

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
