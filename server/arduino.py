import time
import struct
import glob
import traceback
import serial

from cobs import cobs
from multiprocessing import Lock

import arduino_constants as _


def flatten(l): return sum(map(flatten, l), []) if isinstance(l, list) else [l]


FILES = {
    None: '/dev/serial/by-id/usb-Arduino*',
    0: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.1:1.0',
    1: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.2:1.0',
    2: '/dev/serial/by-path/platform-fd500000.pcie-pci-0000:01:00.0-usb-0:1.4:1.0',
}


class Arduino(object):
    def __init__(self, usb_index=None):
        self.set_status(message='object created')
        self.usb_index = usb_index
        self._open_port()
        self.lock = Lock()
        self._last_command_id = 1
        self._hw_config = {'motors': {}}
        self.fence = {}
        self.RESPONSE_FORMAT = ''.join([i[0] for i in _.ResponseHeader])
        self.receive_thread = None
        self.set_status(message='usb port opened')

    def _open_port(self):
        print('opening ardiono port')
        f = glob.glob(FILES[self.usb_index])[0]
        self.ser = serial.Serial(f)

    def _close_port(self):
        self.ser.close()

    def _serial_read(self):
        buffer = []
        while True:
            c = self.ser.read(1)
            if c == b'\x00':
                break
            buffer.append(c)

        buffer = b''.join(buffer)
        buffer = cobs.decode(buffer)
        return buffer

    def _serial_write(self, data):
        encoded = cobs.encode(data)
        self.ser.write(encoded + b'\x00')

    def _send_command(self, data):
        self._serial_write(data)

    def _receive(self):
        while True:
            try:
                ret = self._serial_read()
                response = struct.unpack(self.RESPONSE_FORMAT, ret)

                response_dict = {}
                reading_index = 0
                for i, j in _.ResponseHeader:
                    key = j
                    value = response[reading_index: reading_index + len(i)]
                    reading_index += len(i)
                    if len(value) == 1:
                        value = value[0]
                    response_dict[key] = value

                command_id = response[2]
                # if command_id != 0:
                #     print(response_dict)
                if command_id in self.fence:
                    self.fence[command_id] = response_dict
                self.set_status(data=response)
            except:
                self.set_status(message='receive failed.',
                                traceback=traceback.format_exc())

    def _get_command_id(self):
        self._last_command_id += 1
        return self._last_command_id

    def send_command(self, data, command_id):
        self.fence[command_id] = 0
        self.lock.acquire()
        self._send_command(data)
        self.lock.release()

    def _pack_bytes(self, packet_format, payload):
        format = ''.join([i[0] for i in packet_format])
        data = flatten([payload[i[1]] for i in packet_format if i[1]])
        payload = struct.pack(format, *data)
        return payload

    def _build_single_packet(self, command_type, packet_format, payload):

        # pack payload if packet_format is not None
        if packet_format is not None:
            payload = self._pack_bytes(packet_format, payload)

        command_id = self._get_command_id()
        header = {
            'command_type': command_type,
            'payload_size': len(payload),
            'command_id': command_id,
        }
        format = ''.join([i[0] for i in _.CommandHeader])
        data = [header[i[1]] for i in _.CommandHeader]
        header = struct.pack(format, *data)

        packet = header + payload
        return packet, command_id

    def set_status(self, **kwargs):
        self._status = dict(**kwargs, time=time.time())

    def get_status(self):
        d = dict(self._status)
        d['age'] = time.time() - d['time']
        del d['time']
        return d

    def define_valves(self, pins):
        pins = list(pins) + (_.VALVES_NO - len(pins)) * [_.INVALID_PIN]
        payload = {
            'pins': pins,
        }

        packet, command_id = self._build_single_packet(
            _.COMMAND_TYPE_DEFINE_VALVE, _.DefineValve, payload)
        self.send_command(packet, command_id)
        return command_id

    def set_valves(self, value):
        value = list(value) + (_.VALVES_NO - len(value)) * [None]
        mask = [i is not None for i in value]
        value = [bool(i) for i in value]
        payload = {
            'mask': mask,
            'value': value,
        }

        packet, command_id = self._build_single_packet(
            _.COMMAND_TYPE_SET_VALVE, _.SetValve, payload)

        self.send_command(packet, command_id)
        return command_id

    def define_di(self, pins):
        pins = list(pins) + (_.INPUTS_NO - len(pins)) * [_.INVALID_PIN]
        payload = {
            'pins': pins,
        }

        packet, command_id = self._build_single_packet(
            _.COMMAND_TYPE_DEFINE_DI, _.DefineDI, payload)
        self.send_command(packet, command_id)
        return command_id

    def define_motor(self, motor_definition):
        payload = {
            'motor_no': motor_definition['motor_no'],
            'pin_pulse': motor_definition['pin_pulse'],
            'pin_dir': motor_definition['pin_dir'],
            'pin_limit_p': motor_definition.get('pin_limit_p', _.INVALID_PIN),
            'pin_limit_n': motor_definition.get('pin_limit_n', _.INVALID_PIN),
            'pin_microstep_0': motor_definition.get('pin_microstep_0', _.INVALID_PIN),
            'pin_microstep_1': motor_definition.get('pin_microstep_1', _.INVALID_PIN),
            'pin_microstep_2': motor_definition.get('pin_microstep_2', _.INVALID_PIN),
            'microstep': motor_definition.get('microstep', 1),
            'encoder_ratio': motor_definition.get('encoder_ratio', 1),
            'has_encoder': motor_definition.get('has_encoder', False),
            'encoder_no': motor_definition.get('encoder_no', 0),
            'course': motor_definition.get('course', 0),
            'homing_delay': motor_definition.get('homing_delay', 500),
            'home_retract': motor_definition.get('home_retract', 500),
        }
        self._hw_config['motors'][payload['motor_no']] = payload
        packet, command_id = self._build_single_packet(
            _.COMMAND_TYPE_DEFINE_MOTOR, _.DefineMotor, payload)

        self.send_command(packet, command_id)
        return command_id

    def define_trajectory(self, data):
        format = [
            (_.int32_t, 'index'),
            (_.int32_t, 'zero'),
            (_.uint32_t, 'len_a'),
            (_.uint32_t, 'distance_a'),
            (_.int32_t, 'zero'),
            (_.uint32_t, 'len_d'),
            (_.uint32_t, 'distance_d'),
            (_.uint16_t * len(data['curve_a']), 'curve_a'),
            (_.uint16_t * len(data['curve_d']), 'curve_d'),
        ]

        data = {
            'index': data['index'],
            'zero': 0,
            'len_a': len(data['curve_a']),
            'len_d': len(data['curve_d']),
            'distance_a': sum(data['curve_a'][1::2]),
            'distance_d': sum(data['curve_d'][1::2]),
            'curve_a': data['curve_a'],
            'curve_d': data['curve_d'],
        }
        packet, command_id = self._build_single_packet(
            _.COMMAND_TYPE_DEFINE_TRAJECTORY, format, data)

        self.send_command(packet, command_id)
        return command_id

    def move_motors(self, motor_moves):
        # motor_moves = [{step0, delay0, blocking0, absolute, settling_delay, telorance_soft, telorance_hard}, ...]

        motor_moves = list(motor_moves) + \
            (_.MOTORS_NO - len(motor_moves)) * [{}]
        motor_moves_clean = []
        payload = b''

        for motor in motor_moves:
            if not len(motor):
                flags = 0
            else:
                flags = _.MOVE_MOTOR_FLAGS_ENABLED  # enable
            if motor.get('blocking'):
                flags += _.MOVE_MOTOR_FLAGS_BLOCK
            if motor.get('absolute'):
                flags += _.MOVE_MOTOR_FLAGS_ABSOLUTE
            motor_move_clean = {
                'steps': motor.get('steps', 0),
                'delay': motor.get('delay', 500),
                'flags': flags,
                'settling_delay': motor.get('settling_delay', 0),
                'telorance_soft': motor.get('telorance_soft', 40),
                'telorance_hard': motor.get('telorance_hard', 35000),
            }
            motor_moves_clean.append(motor_move_clean)
            payload += self._pack_bytes(_.MoveMotor, motor_move_clean)

        packet, command_id = self._build_single_packet(
            _.COMMAND_TYPE_MOVE_MOTOR, None, payload)

        self.send_command(packet, command_id)
        return command_id, motor_moves_clean

    def home(self, axis):
        payload = {
            'motor_index': axis,
        }

        packet, command_id = self._build_single_packet(
            _.COMMAND_TYPE_HOME_MOTOR, _.HomeMotor, payload)

        self.send_command(packet, command_id)
        return command_id
