import time
import glob
import traceback
import serial
import json
import asyncio
from collections import abc

from multiprocessing import Lock


def flatten(l): return sum(map(flatten, l), []) if isinstance(l, list) else [l]


FILES = {
    None: '/dev/serial/by-id/usb-Synthetos_TinyG_v2_*',
    0: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0',
    1: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0',
    2: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0',
}


class Arduino(object):
    def __init__(self, usb_index=None):
        self._status = {}
        self._hw_config = {}
        self._encoder_check_enabled = False
        self._encoder_check_status = True
        self.usb_index = usb_index
        self.set_status(message='object created')
        self._open_port()
        self.lock = Lock()
        self._last_command_id = 0
        self._hw_config = {'motors': {}}
        self.receive_thread = None
        self.set_status(message='usb port opened')

    def _open_port(self):
        print('opening ardiono port', self.usb_index)
        f = glob.glob(FILES[self.usb_index])[0]
        self.ser = serial.Serial(f)

    def _close_port(self):
        self.ser.close()

    def _receive(self):
        while True:
            try:
                ret = self.ser.readline()
                response = json.loads(ret)
                # print(ret)
                self.set_status(data=response)
            except:
                tb = traceback.format_exc()
                print(tb)
                self.set_status(message='receive failed.',
                                traceback=tb)

    def send_command(self, data):
        self.lock.acquire()
        data = data + '\n'
        self.ser.write(data.encode())
        self.lock.release()

    def get_command_id(self):
        self._last_command_id += 1
        return self._last_command_id

    async def wait_for_status(self, wait_list):
        while self._status.get('sr.stat', -1) not in wait_list:
            await asyncio.sleep(0.001)

    async def wait_for_command_id(self, command_id):
        while (self._status.get('sr.line', -1) < command_id) and ((self._encoder_check_enabled == False) or (self._encoder_check_status == True)):
            await asyncio.sleep(0.001)

    def set_status(self, message='', traceback='', data={}):
        flatten_data = flatten(data)
        new_status = clean_dictionary(flatten_data)

        if self._encoder_check_enabled:
            if not self.encoder_check(new_status):
                new_status['message'] = 'encoder check failed'
                self.send_command('!')
                time.sleep(.3)
                self.send_command('\x04')
                self._encoder_check_status = False
        if message:
            new_status['message'] = message
        if traceback:
            new_status['traceback'] = traceback

        new_status['time'] = time.time()
        self._status.update(new_status)

    def get_status(self):
        d = dict(self._status)

        d['age'] = time.time() - d['time']
        del d['time']
        return d

    def encoder_check(self, status):
        # 'encoders': {
        #     'posz': ['enc1', 320.0, .1],  # encoder key, ratio, telorance
        # }
        for axis in self._hw_config['encoders']:
            enc_key, ratio, telorance = self._hw_config['encoders'][axis]
            axis_key = 'sr.' + axis
            if axis_key in status:
                g2core_location = status[axis_key]
                encoder_location = status[enc_key] / float(ratio)
                diversion = abs(encoder_location - g2core_location)
                if status.get('sr.stat', -1) != 3:
                    telorance = telorance * 10
                if diversion > telorance:
                    return False
        return True


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


GOOD_KEYS = {'enc1', 'enc2', 'r.msg', 'sr.stat', 'sr.line', 'f.2'}


def clean_key(key):
    if key in GOOD_KEYS:
        return key

    if '.in.' in key:
        return key.replace('.in.', '.in')
    if key.startswith('r.in'):
        return key

    if '.out.' in key:
        return key.replace('.out.', '.out')
    if key.startswith('r.out'):
        return key

    if 'r.pos.' in key:
        return key.replace('r.pos.', 'sr.pos')
    if key.startswith('sr.pos'):
        return key

    if key.startswith('r.stat'):
        return key.replace('r.stat', 'sr.stat')

    return False
