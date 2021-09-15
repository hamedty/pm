import time
import glob
import traceback
import serial
import json
import asyncio
from collections import abc

from multiprocessing import Lock


def flatten(l): return sum(map(flatten, l), []) if isinstance(l, list) else [l]


class HW_PANIC_EXCEPTION(Exception):
    pass


FILES = {
    None: '/dev/serial/by-id/usb-Synthetos_TinyG_v2_*',
    0: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0',
    1: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0',
    2: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.3:1.0',
}


class Arduino(object):
    def __init__(self, usb_index=None):
        self._status = {}
        self._hw_config = {}
        self.usb_index = usb_index
        self.lock = Lock()
        self._last_command_id = 0
        self.stat_code = 0
        self._hw_config = {'motors': {}}
        self.receive_thread = None
        self._status_out_queue = None
        self._debug = False
        self.set_status(message='object created')
        self._open_port()
        self.set_status(message='usb port opened')

    def _open_port(self):
        print('opening ardiono port', self.usb_index)
        f = glob.glob(FILES[self.usb_index])[0]
        self.ser = serial.Serial(f)

    def restart(self):
        data = '\x18\n'.encode()
        self.lock.acquire()
        self.ser.write(data)
        time.sleep(1)
        self._open_port()
        self.stat_code = 0
        self._last_command_id = 0
        self.lock.release()

    def _close_port(self):
        self.ser.close()

    def _receive(self):
        while True:
            try:
                ret = self.ser.readline()
            except:
                time.sleep(.1)
            response = json.loads(ret)
            if self._debug:
                print('response:', response)
            self.set_status(data=response)

    def send_command(self, data):
        clean_data = []
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            if line[0] == ';':
                continue
            clean_data.append(line)
        data = '\n'.join(clean_data)
        self._send_command(data)

    def _send_command(self, data):
        data += '\n'
        data = data.encode()

        self.lock.acquire()
        self.ser.write(data)
        if self._debug:
            print('command', data)
        self.lock.release()

    def get_command_id(self):
        self._last_command_id += 1
        return self._last_command_id

    async def wait_for_status(self, wait_list):
        while self._status.get('r.stat', -1) not in wait_list:
            await asyncio.sleep(0.001)

    async def wait_for_command_id(self, command_id):
        while (self._status.get('r.line', -1) < command_id):
            if self._status.get('r.stat', -1) in {13}:
                raise HW_PANIC_EXCEPTION()
            await asyncio.sleep(0.001)
        if self.stat_code:
            raise HW_PANIC_EXCEPTION(self.stat_code)

    def set_status(self, message='', traceback='', data={}):
        flatten_data = flatten(data)
        new_status = clean_dictionary(flatten_data)
        self.stat_code = max(new_status.get('f.2', 0), self.stat_code)
        if message:
            new_status['message'] = message
        if traceback:
            new_status['traceback'] = traceback

        new_status['time'] = time.time()
        self._status.update(new_status)
        if self._status_out_queue is not None:
            try:
                self._status_out_queue.put_nowait(self.get_status())
            except asyncio.QueueFull:
                pass

    def get_status(self):
        d = dict(self._status)

        d['age'] = time.time() - d['time']
        d['stat_code'] = self.stat_code
        del d['time']
        return d

    def check_encoder(self, axis, desired_location):  # axis = 'x'
        # 'encoders': {
        #     'posz': ['enc1', 320.0, .1],  # encoder key, ratio, telorance
        # }

        enc_key, ratio, telorance = self._hw_config['encoders']['pos' + axis]
        axis_key = 'r.pos' + axis

        g2core_location = self._status[axis_key]
        encoder_location = self._status[enc_key] / float(ratio)
        diversion_g2core = abs(encoder_location - g2core_location)
        result = (diversion_g2core < telorance)
        diversion_desired = abs(encoder_location - desired_location)
        reached = (diversion_desired < telorance)
        return result, reached, g2core_location, encoder_location


def flatten(dictionary, parent_key=False, separator='.'):
    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, abc.MutableMapping):
            items.extend(flatten(value, new_key, separator).items())
        elif isinstance(value, list):
            for k, v in enumerate(value):
                items.extend(flatten({str(k + 1): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


def clean_dictionary(dictionary):
    new_dict = {}
    for key in dictionary:
        value = dictionary[key]
        key = clean_key(key)
        if key:
            new_dict[key] = value
    return new_dict


GOOD_KEYS = {'enc1', 'enc2', 'r.msg', 'f.2', 'r.stat', 'r.line', 'er.st'}


def clean_key(key):
    if '.in.' in key:
        return key.replace('.in.', '.in')
    if key.startswith('r.in'):
        return key

    if '.out.' in key:
        return key.replace('.out.', '.out')
    if key.startswith('r.out'):
        return key

    if key.startswith('r.sr.'):
        key = key.replace('r.sr.', 'r.')

    if key.startswith('sr.'):
        key = key.replace('sr.', 'r.')

    if '.pos.' in key:
        return key.replace('.pos.', '.pos')
    if key.startswith('r.pos'):
        return key

    if key in GOOD_KEYS:
        return key

    return False
