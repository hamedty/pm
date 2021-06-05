from .node import Node
from .trajectory import CURVE_STATION
import os
import json

PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.dirname(PATH)
BASE_PATH = os.path.dirname(SERVER_PATH)
VISION_ANNOTATION_FILE = os.path.join(BASE_PATH, 'models/annotaion.json')

with open(VISION_ANNOTATION_FILE) as f:
    VISION_ANNOTATION = json.loads(f.read())


class Station(Node):
    type = 'station'
    arduino_reset_pin = 21
    hw_config_base = {
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
                'home_retract': 300,
                'microstep': 2500,
                'has_encoder': True,
                'encoder_no': 0,
                'encoder_ratio': 3,
            },
        ],
        'di': [
            28,  # jack verification
            24,  # gate verification
        ],
        'points': {
            'H_ALIGNING': 21500,
            'H_PUSH': 23000,
        }

    }
    curves = [CURVE_STATION]

    async def send_command_create_camera(self):
        annotation_data = VISION_ANNOTATION[str(self.ip_short)]
        roi = VISION_ANNOTATION
        command = {
            'verb': 'create_camera',
            'dosing_roi': [annotation_data['dosing_roi']],
            'holder_roi': [annotation_data['holder_roi']],
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

    def ready_for_command(self):
        return 'm4-main' in self._status.get('data', {})

    def set_home_retract(self, motor_index, value):
        self.hw_config['motors'][motor_index]['home_retract'] = value

    def goto(self, location, offset=0, **kwargs):
        if isinstance(location, str):
            h = self.hw_config['points'][location] + offset
        else:
            h = location
        move = {'steps': h, 'absolute': True}
        move.update(kwargs)
        moves = [{}, {}, {}, move]
        return self.send_command({'verb': 'move_motors', 'moves': moves}, assert_success=True)
