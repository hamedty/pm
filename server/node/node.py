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


class WAIT_METRIC_TIMEOUT_EXCEPTION(Exception):
    pass


class ConnectionPool(object):
    def __init__(self, ip, port, count=8):
        self.ip = ip
        self.port = port
        self.count = count
        self.pool = []
        self.occupied = set()
        self.lock = asyncio.Lock()

    async def connect(self):
        for i in range(self.count):
            reader, writer = await asyncio.open_connection(self.ip, self.port)
            self.pool.append((reader, writer))

    def ready(self):
        return len(self.pool) > len(self.occupied)

    async def get_socket(self):
        async with self.lock:
            for i in range(len(self.pool)):
                if i not in self.occupied:
                    self.occupied.add(i)
                    return self.pool[i], i
            raise Exception("running out of connection in pool")

    async def release_socket(self, i):
        async with self.lock:
            self.occupied.remove(i)


class Node(object):
    HOMMING_RETRIES = 2
    HOMMED_AXES = ['a']
    AUTO_CLEAR_HOLD = False

    def __init__(self, name, ip, arduino_id=None):
        # self.set_status(message='node instance creating')
        self.name = name
        self.ip = ip
        self.ip_short = int(self.ip.split('.')[-1])
        self.arduino_id = arduino_id
        self.hw_config = copy.deepcopy(self.hw_config_base)
        self.g2core_config = copy.deepcopy(self.g2core_config_base)
        self.connection_pool = ConnectionPool(self.ip, 2000, 5)

        # self.set_status(message='node instance created')
        self.homed = False
        self.events = {}
        self.errors = {}
        self.last_hold_clear = 0

    def set_system(self, system):
        self.system = system

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
        await self.set_status(message='Trying to connect to RPI')
        while not self.connection_pool.ready():
            try:
                await self.connection_pool.connect()
            except:
                print(traceback.format_exc())
                print('retrying to connect to', self.name)
                await asyncio.sleep(.5)
                continue

            await self.set_status(message='socket connected')

        await self.create_arduino()
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

    async def send_command(self, command, assert_success=True):
        command['arduino_index'] = self.arduino_id
        command_str = json.dumps(command) + '\n'
        command_str = command_str.encode()

        socket, index = await self.connection_pool.get_socket()
        reader, writer = socket
        writer.write(command_str)
        line = await reader.readline()
        await self.connection_pool.release_socket(index)

        line = json.loads(line)
        if 'status' in line:
            await self.set_status(**line['status'])
        if assert_success:
            assert line['success'], (line, self.ip, self.arduino_id)
        elif not line['success']:
            print('send command silenly failed:', line)
        return line['success'], line

    async def loop(self):
        while True:
            if (time.time() - self._status['time']) > 0.25:
                await self.send_command({'verb': 'get_status'})
                await asyncio.sleep(0.25)

    async def restart_arduino(self):
        command = {
            'verb': 'restart_arduino',
        }
        await self.send_command(command)
        await self.create_arduino()

    async def create_arduino(self):
        # update rpi-scripts file
        await self.scp_to('./rpi_scripts.py', '~/server/')

        # calc rois
        if self.hw_config.get('cameras'):
            self.calc_rois()

        # send command
        command = {
            'verb': 'create_arduino',
            'g2core_config': self.g2core_config,
            'hw_config': self.hw_config,
        }
        await self.send_command(command)

    async def set_valves(self, values):
        N = min(len(self.hw_config['valves']), len(values))
        data = {}
        for i in range(1, N + 1):
            data[i] = values[i - 1]
            if data[i] is not None:
                data[i] = int(data[i])
        data = {'out': data}
        return await self.send_command_raw(json.dumps(data), wait_start=[], wait_completion=False)

    async def G1(self, **kwargs):
        # if not self.homed:
        #     raise
        # kwargs: x, y, z, feed
        command = {'verb': 'G1'}
        command.update(kwargs)

        while True:
            success, line = await self.send_command(command, assert_success=False)
            if success:
                return success, line
            error = {
                'message': 'خطا در حرکت - احتمال تصادف',
                'location_name': self.name,
                'details': line,
                'type': 'error',
            }
            print(error)
            error_clear_event, error_id = await self.system.register_error(error)
            await error_clear_event.wait()
            command['correct_initial'] = True

    def ready_for_command(self):
        return 'enc1' in self._status

    async def set_status(self, **kwargs):
        self._status = kwargs
        self._status['time'] = time.time()

        if 'r.stat' in kwargs:
            if kwargs['r.stat'] == 6:
                asyncio.create_task(self.raise_hold_error())
            # elif self.is_hold_error_raised():
            #     await self.clear_hold_error()

        # if 'errors' in kwargs:
        #     errors = kwargs['errors']
        #     if 'no_cartridge' in errors:
        #         await self.raise_no_cartridge_error()

    async def raise_hold_error(self):
        if self.is_hold_error_raised():
            return
        self.errors['holded'] = {'status': 'raising'}
        error = {
            'message': 'خطا در حرکت',
            'location_name': self.name,
            'details': 'احتمالا تصادف رخ داده!',
            'type': 'error',
        }
        clear_cb = self.clear_hold_error

        # Foregiveness
        foregive = False
        if self.AUTO_CLEAR_HOLD:
            if time.time() - self.last_hold_clear > 60:
                foregive = True
        if foregive:
            await self.clear_hold_error()
            return

        print(error)
        _, error_id = await self.system.register_error(error, clear_cb)
        self.errors['holded']['error_id'] = error_id
        self.errors['holded']['status'] = 'raised'

    def is_hold_error_raised(self):
        return 'holded' in self.errors

    async def clear_hold_error(self):
        if self.errors['holded']['status'] == 'clearing':
            return

        self.errors['holded']['status'] = 'clearing'
        self.last_hold_clear = time.time()
        await asyncio.sleep(.8)

        await self.set_eac(eac1=0, eac2=0, wait_start=[], wait_completion=False)
        # detect axis error
        enc_configs = self.hw_config['encoders']
        for axis_key in enc_configs:
            # axis_key = 'posx'
            axes = axis_key[-1].upper()
            feedrate = 1000
            # encoder key, ratio, telorance_soft, telorance_hard
            # 'posx': ['enc2', 120.0, 1.0, 5.0],
            # 'posy': ['enc1', 120.0, 1.0, 5.0],
            enc_key, ratio, telorance, _ = enc_configs[axis_key]
            enc_value = self._status[enc_key]
            enc_location = float(enc_value) / ratio
            g2_location = self._status['r.' + axis_key]
            error = abs(enc_location - g2_location)
            if error < telorance:
                continue
            message = f'Correction: {self.name} Axes: {axes} From: {enc_location:.2f} To: {g2_location:.2f}'
            print(message)
            # update g2core location
            await self.send_command_raw(f'{{gc2:"G28.3 {axes}{enc_location}"}}', wait_start=[], wait_completion=False)
            await asyncio.sleep(.1)
            # g1 to g2core_old location
            await self.send_command_raw(f'{{gc2:"G1 {axes}{g2_location} F{feedrate}"}}', wait_start=[], wait_completion=False)
            sleep_time = error / feedrate * 60
            await asyncio.sleep(sleep_time + .3)

        # resume
        await self.send_command_raw('~', wait_start=[], wait_completion=False)
        await asyncio.sleep(.1)
        await self.set_eac(*self.hw_config['eac'], wait_start=[], wait_completion=False)
        await asyncio.sleep(.1)

        del self.errors['holded']

    def get_status(self):
        data = {'connected': self.connection_pool.ready(), 'age': 0}

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
                await self.set_eac(*self.hw_config['eac'])
                self.homed = True
                print('%s Homed!' % self.name)
                return
            except:
                print('repeating home - homming failed', self.name)
        raise Exception('Homing Failed')

    async def set_eac(self, eac1=None, eac2=None, **kwargs):
        if eac1 is not None:
            await self.send_command_raw(f"{{eac1: {eac1}}}", **kwargs)
        if eac2 is not None:
            await self.send_command_raw(f"{{eac2: {eac2}}}", **kwargs)

    def get_loc(self, axis):
        # axis in {'x', 'y', 'z'}
        enc_name, enc_ratio, telorance_soft, telorance_hard = self.hw_config[
            'encoders']['pos' + axis]
        enc_location = self._status[enc_name] / float(enc_ratio)
        # g2_location = await self.read_metric('pos' + axis)
        g2_location = self._status['r.pos' + axis]
        error = abs(g2_location - enc_location)
        assert error < telorance_soft, f'get_loc failed for {self.name}, error = {error}'
        return g2_location, enc_location, telorance_soft

    def get_enc_loc(self, axis):
        # axis in {'x', 'y', 'z'}
        enc_name, enc_ratio, _, _ = self.hw_config['encoders']['pos' + axis]
        enc_location = self._status[enc_name] / float(enc_ratio)
        return enc_location

    def is_at_loc(self, **kwargs):
        # x=10, y=20, z=30
        for axis in kwargs:
            desired_location = kwargs[axis]
            g2_location, enc_location, telorance = self.get_loc(axis)
            if abs(desired_location - enc_location) > telorance:
                return False
        return True

    async def is_homed(self):
        res = [await self.read_metric('hom' + axis) == 1 for axis in self.HOMMED_AXES]
        return all(res)

    async def read_metric(self, query, response=None):
        if response is None:
            response = 'r.' + query
        command = {
            'verb': 'read_metric',
            'query': query,
            'response': response,
        }
        success, line = await self.send_command(command)
        return line['result']

    async def wait_metric(self, metric, expected=1, timeout=None):
        start_time = time.time()
        while await self.read_metric(metric) != expected:
            await asyncio.sleep(0.001)

            if timeout is None:
                continue
            if time.time() > (start_time + timeout):
                raise WAIT_METRIC_TIMEOUT_EXCEPTION()

    async def send_command_from_hmi(self, command):
        if command['verb'] == 'dump_frame':
            command['components'] = ['holder', 'dosing']
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
            await self.set_valves([0])
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

        elif command['verb'] == 'align' and command['component'] == 'dosing':
            await self.set_valves([0])
            await self.G1(z=self.hw_config['H_ALIGNING'], feed=10000)
            res = await self.send_command(command)
            print(res)
            await self.set_valves([0])
            await self.G1(z=100, feed=10000)

        elif command['verb'] == 'home':
            await self.home()
        else:
            return await self.send_command(command)
