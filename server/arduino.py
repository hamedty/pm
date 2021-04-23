import time
import struct
import serial
from cobs import cobs
import argparse
from multiprocessing import Lock

import arduino_constants as _


class Arduino(object):
    def __init__(self):
        # self._open_port()
        self.lock = Lock()
        self._last_command_id = 0

    def _open_port(self):
        self.ser = serial.Serial('/dev/serial/by-id/usb-Arduino_Arduino_Due-if00')

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
        data = struct.pack(self.FORMAT, *data)
        self._serial_write(data)
        ret = self._serial_read()
        # print(ret)
        response = struct.unpack(self.RESPONSE, ret)
        # response = struct.unpack('I' * 1000, ret)
        print(response)
        status_code = response[0]
        if status_code == SUCCESS:
            return response
        raise Exception('Invalid response from firmware: %d' % response)

    def _get_command_id(self):
        self._last_command_id += 1
        return self._last_command_id

    def send_command(data):
        self.lock.acquire()
        result = self._send_command(data)
        self.lock.release()
        return result

    def _build_single_packet(self, command_type, packet_format, payload):
        format = ''.join([i[0] for i in packet_format])
        data = sum([payload[i[1]] for i in packet_format], [])
        payload = struct.pack(format, *data)

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

    def define_valves(self, *pins):
        pins = list(pins) + (_.VALVES_NO - len(pins)) * [_.INVALID_PIN]
        payload = {
            'pins': pins,
        }

        packet, command_id = self._build_single_packet(_.COMMAND_TYPE_DEFINE_VALVE, _.DefineValve, payload)
        return packet, command_id

    def set_valves(self, *value):
        value = list(value) + (_.VALVES_NO - len(value)) * [None]
        mask = [i is not None for i in value]
        value = [bool(i) for i in value]
        payload = {
            'mask': mask,
            'value': value,
        }

        packet, command_id = self._build_single_packet(_.COMMAND_TYPE_SET_VALVE, _.SetValve, payload)
        return packet, command_id

    def define_motor(self, motor_definition):
        payload = {
            'motor_no': motor_definition['motor_no'],
            'pin_pulse': motor_definition['pin_pulse'],
            'pin_dir': motor_definition['pin_dir'],
            'pin_limit_p': motor_definition.get('pin_limit_p', INVALID_PIN),
            'pin_limit_n': motor_definition.get('pin_limit_n', INVALID_PIN),
            'pin_microstep_0': motor_definition.get('pin_microstep_0', INVALID_PIN),
            'pin_microstep_1': motor_definition.get('pin_microstep_1', INVALID_PIN),
            'pin_microstep_2': motor_definition.get('pin_microstep_2', INVALID_PIN),
            'microstep': motor_definition.get('microstep', 1),
            'encoder_ratio': motor_definition.get('encoder_ratio', 1),
            'has_encoder': motor_definition.get('has_encoder', False),
            'encoder_no': motor_definition.get('encoder_no', 0),

        }

        packet, command_id = self._build_single_packet(_.COMMAND_TYPE_DEFINE_MOTOR, _.DefineMotor, payload)
        return packet, command_id


def main():
    arduino = Arduino()
    print(arduino.define_valves(1, 2, 3))


if __name__ == '__main__':
    main()
