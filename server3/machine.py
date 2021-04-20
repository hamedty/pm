import time
import struct
import serial
from cobs import cobs
import termios
import argparse
from multiprocessing import Lock


SUCCESS = 0


class Machine(object):
    MOTOR_COUNT = 4
    VALVES_COUNT = 6

    SIZEOF_COMMAND = 44
    ALIGNMENT_BYTES = 1
    FORMAT = ''.join([
        # Motor
        'i' * MOTOR_COUNT,  # int32_t steps_raw[MOTOR_COUNT];
        'i' * MOTOR_COUNT,  # int32_t speed[MOTOR_COUNT];
        '?' * MOTOR_COUNT,  # Run Blocking

        # Pneumatic
        '?' * VALVES_COUNT,

        # Homming
        '?',


        # alignment
        '?' * ALIGNMENT_BYTES,
    ])

    RESPONSE = ''.join([
        'I',  # uint32_t status_code
        'I',  # uint32_t encoder
        'I' * 3,  # reserve
    ])

    def __init__(self, encoder_compensate_non_linearity=True):
        assert struct.calcsize(
            self.FORMAT) == self.SIZEOF_COMMAND, struct.calcsize(self.FORMAT)
        self._open_port()
        self.lock = Lock()

    def _open_port(self):
        self.ser = serial.Serial(
            '/dev/serial/by-id/usb-Arduino_Arduino_Due-if00', baudrate=115200)

    def _serial_read(self):
        buffer = []
        while True:
            c = self.ser.read(1)
            if not c:
                raise Exception('timeout')
            if c == b'\x00':
                break
            buffer.append(c)

        buffer = b''.join(buffer)
        buffer = cobs.decode(buffer)
        return buffer

    def _serial_write(self, data):
        encoded = cobs.encode(data)
        for i in range(5):
            try:
                self.ser.write(encoded + b'\x00')
                return
            except:
                print('serial port failed.....')
                self.ser.close()
                self._open_port()

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

    def send_command(self,

                     m1=0,
                     d1=100,
                     b1=1,

                     m2=0,
                     d2=100,
                     b2=1,

                     m3=0,
                     d3=100,
                     b3=1,

                     m4=0,
                     d4=100,
                     b4=1,

                     v1=0,
                     v2=0,
                     v3=0,
                     v4=0,
                     v5=0,
                     v6=0,
                     dance=0,
                     home=0,
                     ):
        if dance:

            # m1 6400 -> 1 rev
            # m4 800 -> 1 rev -> 8mm
            # pen 11mm/rev
            m1 = dance * 6400.
            m4 = dance * 11. / 8. * 800
            d4 = d1 * m1 / m4

        # print(sd, sa, delay_4)
        data = [
            m1, m2, m3, m4,
            d1, d2, d3, d4,
            b1, b2, b3, b4,
            v1, v2, v3, v4, v5, v6,
            home,
        ]
        data += [0] * self.ALIGNMENT_BYTES

        data = [int(d) for d in data]

        self.lock.acquire()
        result = self._send_command(data)
        self.lock.release()
        return result

    def bootup(self):
        self.send_command(home=1)
        #
        # # comming down
        # self.send_command(vdc=1)
        input('place dosing and holder')
        self.send_command(sa=5950, vdc=1, vh=1)
        time.sleep(0.25)
        self.send_command(vdc=1, vd=1, vh=1)
        time.sleep(0.25)
        self.send_command(vd=1, vh=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m1', nargs='?', type=int)
    parser.add_argument('-d1', nargs='?', type=int)
    parser.add_argument('-b1', nargs='?', type=bool)

    parser.add_argument('-m2', nargs='?', type=int)
    parser.add_argument('-d2', nargs='?', type=int)
    parser.add_argument('-b2', nargs='?', type=bool)

    parser.add_argument('-m3', nargs='?', type=int)
    parser.add_argument('-d3', nargs='?', type=int)
    parser.add_argument('-b3', nargs='?', type=bool)

    parser.add_argument('-m4', nargs='?', type=int)
    parser.add_argument('-d4', nargs='?', type=int)
    parser.add_argument('-b4', nargs='?', type=bool)

    parser.add_argument('-v1', nargs='?', type=int)
    parser.add_argument('-v2', nargs='?', type=int)
    parser.add_argument('-v3', nargs='?', type=int)
    parser.add_argument('-v4', nargs='?', type=int)
    parser.add_argument('-v5', nargs='?', type=int)
    parser.add_argument('-v6', nargs='?', type=int)
    parser.add_argument('-dance', nargs='?', type=int)
    parser.add_argument('-home', nargs='?', type=int)
    parser.add_argument('-boot', nargs='?', type=int)

    args = vars(parser.parse_args())
    args = {k: v for k, v in args.items() if v is not None}

    machine = Machine()
    if args.get('boot'):
        machine.bootup()
    else:
        machine.send_command(**args)


if __name__ == '__main__':
    main()
