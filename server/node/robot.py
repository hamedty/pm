from .node import Node

# 1600 pulse  / rev


class Robot(Node):
    type = 'robot'
    arduino_reset_pin = 2
    valves = [15, 16]
    hw_config = {
        'valves': [36, 39, 38, 41, 40, 43, 42, 45, 44, 47],
        'motors': [
            {  # AXIS 1 - Up & Down
                'pin_pulse': 15,
                'pin_dir': 14,
                'pin_limit_n': 50,
                'pin_limit_p': 51,
                'microstep': 2500,
                'course': 10000,
                'homing_delay': 200,
                'home_retract': 400,
                'has_encoder': True,
                'encoder_no': 0,
            },
            {  # AXIS 2 - Front & Back
                'pin_pulse': 17,
                'pin_dir': 16,
                'pin_limit_n': 49,
                'pin_limit_p': 48,
                'microstep': 2500,
                'course': 30000,
                'homing_delay': 200,
                'home_retract': 400,
                'has_encoder': True,
                'encoder_no': 1,
            },
        ],
    }

    def __init__(self, name, ip, arduino_id):
        self.arduino_id = arduino_id
        super(Robot, self).__init__(name, ip)

    async def send_command(self, command):
        command.update(arduino_index=self.arduino_id)
        return await super(Robot, self).send_command(command)

    def set_status(self, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']
            data = data[3:-2]
            data = dict(zip(['enc1', 'enc2', 'di1', 'di2', 'm1', 'm2'], data))
            kwargs['data'] = data
        super(Robot, self).set_status(**kwargs)


ROBOT_1_IP = '192.168.44.100'
ROBOTS = [
    Robot('Robot 1', ROBOT_1_IP, 0),
    Robot('Robot 2', ROBOT_1_IP, 1),
]
