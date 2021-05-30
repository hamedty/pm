from .robot import Robot
from .robot import ROBOT_1_IP
from .trajectory import CURVE_RAIL


class Rail(Robot):
    type = 'rail'
    hw_config = {
        'valves': [47, 44],
        'motors': [
            {
                'pin_pulse': 17,
                'pin_dir': 16,
                'pin_limit_n': 48,
                'microstep': 2500,
                'course': 76100,  # 80000
                'homing_delay': 200,
                'home_retract': 200,
                'has_encoder': True,
                'encoder_no': 0,
                'encoder_ratio': 2,
            },
        ],
        'di': [48],

    }
    curves = [CURVE_RAIL]
    center_point = 40000

    def set_status(self, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']
            data = data[3:-2]
            data = dict(
                zip(['enc', 'enc2', 'di-limit', 'di2', 'm', 'm2'], data))
            del data['di2']
            del data['enc2']
            del data['m2']
            # data['m'] = MOTOR_STATUS_ENUM[data['m']]
            kwargs['data'] = data
        super(Robot, self).set_status(**kwargs)


RAILS = [
    Robot('Rail 1', ROBOT_1_IP, 2),
]
