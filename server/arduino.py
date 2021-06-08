import time
import glob
import traceback
import serial
import json

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
        self.set_status(message='object created')
        self.usb_index = usb_index
        self._open_port()
        self.lock = Lock()
        self._last_command_id = 1
        self._hw_config = {'motors': {}}
        self.fence = {}
        self.receive_thread = None
        self.set_status(message='usb port opened')

    def _open_port(self):
        print('opening ardiono port', self.usb_index)
        f = glob.glob(FILES[self.usb_index])[0]
        self.ser = serial.Serial(f)

    def _close_port(self):
        self.ser.close()

    def _serial_read(self):
        return self.ser.readline()

    def _receive(self):
        while True:
            try:
                ret = self._serial_read()
                response = json.loads(ret)

                # if command_id != 0:
                #     print(response_dict)
                # if command_id in self.fence:
                #     self.fence[command_id] = response_dict
                self.set_status(data=response)
            except:
                self.set_status(message='receive failed.',
                                traceback=traceback.format_exc())

    # def _get_command_id(self):
    #     self._last_command_id += 1
    #     return self._last_command_id

    # def _build_single_packet(self, command_type, packet_format, payload):
    #     command_id = self._get_command_id()

    def send_command(self, data, command_id=None):
        print('------------')
        print(data)
        # self.fence[command_id] = 0
        self.lock.acquire()
        self.ser.write(data.encode())
        self.lock.release()

    def send_dict(self, data):
        self.send_raw(json.dumps(data))

    def send_raw(self, data):
        self.send_command(data + '\n')

    def set_status(self, **kwargs):
        self._status.update(kwargs)
        self._status['time'] = time.time()
        print(self._status)

    def get_status(self):
        d = dict(self._status)
        d['age'] = time.time() - d['time']
        del d['time']
        return d
