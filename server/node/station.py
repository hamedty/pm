from .node import Node
from .trajectory import CURVE_STATION


class Station(Node):
    type = 'station'
    arduino_reset_pin = 21
    hw_config = {
        'valves': [
            8,  # holder gripper
            7,  # dosing gripper
            6,  # main jack
            5,  # dosing base
            4,  # gate
            3,  # not connected
        ],
        'motors': [
            {  # holder motor
                'pin_pulse': 43,
                'pin_dir': 42,
                'pin_microstep_0': 46,
                'pin_microstep_1': 45,
                'pin_microstep_2': 44,
                'microstep': 32,
            },
            {  # not connected
                'pin_pulse': 25,
                'pin_dir': 23,
                'pin_microstep_0': 31,
                'pin_microstep_1': 29,
                'pin_microstep_2': 27,
                'microstep': 32,
            },
            {  # dosing motor
                'pin_pulse': 48,
                'pin_dir': 47,
                'pin_microstep_0': 51,
                'pin_microstep_1': 50,
                'pin_microstep_2': 49,
                'microstep': 32,
            },
            {  # Main ball-screw motor
                'pin_pulse': 35,
                'pin_dir': 33,
                'pin_limit_n': 28,
                'course': 24000,
                'homing_delay': 200,
                'home_retract': 100,
                'microstep': 2500,
                'has_encoder': True,
                'encoder_no': 0,
                'encoder_ratio': 3,
            },
        ],
        'di': [
            26,  # jack verification
            24,  # gate verification
        ],

    }
    curves = [CURVE_STATION]

    async def send_command_create_camera(self):
        command = {
            'verb': 'create_camera',
        }
        return await self.send_command(command)

    def set_status(self, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']
            data = data[3:-2]
            data = dict(
                zip(['enc', 'enc2', 'di-jack', 'di-gate', 'm1-holder', 'm2', 'm3-dosing', 'm4-main'], data))
            # data['enc'] = round(data['enc'] / 3.0)
            del data['enc2']
            del data['m2']
            # data['m1-holder'] = MOTOR_STATUS_ENUM[data['m1-holder']]
            # data['m3-dosing'] = MOTOR_STATUS_ENUM[data['m3-dosing']]
            # data['m4-main'] = MOTOR_STATUS_ENUM[data['m4-main']]

            kwargs['data'] = data
        super(Station, self).set_status(**kwargs)


STATIONS = [
    # First Five
    Station('Station 1', '192.168.44.101'),
    Station('Station 2', '192.168.44.102'),
    Station('Station 3', '192.168.44.103'),
    Station('Station 4', '192.168.44.104'),
    Station('Station 5', '192.168.44.105'),

    # Second Five
    Station('Station 6', '192.168.44.106'),
    Station('Station 7', '192.168.44.107'),
    Station('Station 8', '192.168.44.108'),
    Station('Station 9', '192.168.44.109'),
    Station('Station 10', '192.168.44.110'),
]
