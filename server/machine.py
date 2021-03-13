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
        'H',  # uint16_t status_code
        'H' * 3,  # reserve
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
        response = struct.unpack(self.RESPONSE, ret)
        # print(response)
        status_code = response[0]
        if status_code == SUCCESS:
            return response
        raise Exception('Invalid response from firmware: %d' % response)

    def send_command(self,

                     st=0,
                     delay_1=3000,
                     run_blocking_1=1,

                     sd=0,
                     delay_2=1000,
                     run_blocking_2=1,

                     sh=0,
                     delay_3=1000,
                     run_blocking_3=1,

                     sa=0,
                     delay_4=5000,
                     run_blocking_4=1,

                     valve1=0,
                     vdn=0,
                     vdc=0,
                     vd=0,
                     vh=0,
                     vp=0,
                     dance=0,
                     home=0,
                     ):
        if dance:
            sd = int(dance * 400)
            sa = int(sd * 11. / 8.)
            delay_4 = int(delay_2 * 8. / 11.)
        # print(sd, sa, delay_4)
        data = [
            st, sd, sh, int(sa),
            delay_1, delay_2, delay_3, delay_4,
            run_blocking_1, run_blocking_2, run_blocking_3, run_blocking_4,
            valve1, vdn, vdc, vd, vh, vp,
            home,
        ]
        data += [0] * self.ALIGNMENT_BYTES

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
    parser.add_argument('-sa', nargs='?', type=int)
    parser.add_argument('-delay_1', nargs='?', type=int)
    parser.add_argument('-run_blocking_1', nargs='?', type=bool)

    parser.add_argument('-sd', nargs='?', type=int)
    parser.add_argument('-delay_2', nargs='?', type=int)
    parser.add_argument('-run_blocking_2', nargs='?', type=bool)

    parser.add_argument('-sh', nargs='?', type=int)
    parser.add_argument('-delay_3', nargs='?', type=int)
    parser.add_argument('-run_blocking_3', nargs='?', type=bool)

    parser.add_argument('-st', nargs='?', type=int)
    parser.add_argument('-delay_4', nargs='?', type=int)
    parser.add_argument('-run_blocking_4', nargs='?', type=bool)

    parser.add_argument('-valve1', nargs='?', type=int)
    parser.add_argument('-vdn', nargs='?', type=int)
    parser.add_argument('-vdc', nargs='?', type=int)
    parser.add_argument('-vd', nargs='?', type=int)
    parser.add_argument('-vh', nargs='?', type=int)
    parser.add_argument('-vp', nargs='?', type=int)
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
