from .robot import Robot
from .robot import ROBOT_1_IP


class Rail(Robot):
    type = 'rail'
    hw_config = {
        'valves': [47, 44],
        'motors': [
            {
                'pin_pulse': 15,
                'pin_dir': 14,
                'pin_limit_n': 48,
                'pin_limit_p': 49,
                'microstep': 2500,  # step / mm
                'course': 10000,  # mm
                'homing_delay': 200,  # mm / s
                'home_retract': 400,  # mm
                'has_encoder': True,
                'encoder_no': 0,
            },
        ],
        'di': [50, 51],
    }


RAILS = [
    Robot('Rail 1', ROBOT_1_IP, 2),
]
