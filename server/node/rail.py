import asyncio
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

    def ready_for_command(self):
        return 'm' in self._status.get('data', {})

    async def goto(self, y):
        return await super(Rail, self).goto(y=y)

    async def is_homed(self, telorance=50):
        home_pos = 40000
        while True:
            cur_status = self.get_status()
            age = cur_status['age']
            if age < 0.3:
                break
            await asyncio.sleep(.005)

        cur_pos = cur_status['data']['enc']
        diversion = abs(cur_pos - home_pos)
        assert (diversion < telorance), diversion


RAILS = [
    Robot('Rail 1', ROBOT_1_IP, 2),
]
