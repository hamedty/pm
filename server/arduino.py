import time
import glob
import traceback
import serial
import json
import asyncio

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
        self.set_status(message='object created')
        self.usb_index = usb_index
        self._open_port()
        self.lock = Lock()
        self._last_command_id = 1
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

    def _get_command_id(self):
        self._last_command_id += 1
        self._last_command_id %= 1000
        return self._last_command_id

    def send_command(self, data):
        command_id = self._get_command_id()
        self.lock.acquire()
        data = data + '\n'
        self.ser.write(data.encode())
        self.lock.release()

    async def wait_for_status(self, status_code=3):
        while self._status.get('stat', -1) != status_code:
            await asyncio.sleep(0.001)

    def set_status(self, message='', traceback='', data={}):
        if 'enc1' in data:
            self._status['enc1'] = data['enc1']
            self._status['enc2'] = data['enc2']
        for key in ('posx', 'posy', 'posz', 'stat', 'n', 'line', 'in'):
            if key in data.get('sr', {}):
                self._status[key] = data['sr'][key]
        if message:
            self._status['message'] = message

        self._status['time'] = time.time()

    def get_status(self):
        d = dict(self._status)

        d['age'] = time.time() - d['time']
        del d['time']
        return d
