from .node import Node


class Robot(Node):
    type = 'robot'
    arduino_reset_pin = 2
    valves = [15, 16]
    hw_config = {
        'valves': [47, 44, 45, 42, 43, 40, 41, 38, 39, 36],
        'motors': [
            {
                'pin_pulse': 15,
                'pin_dir': 14,
                'pin_limit_n': 48,
                'pin_limit_p': 49,
                'microstep': 2500,
                'course': 10000,
                'homing_delay': 200,
                'home_retract': 400,
                'has_encoder': True,
                'encoder_no': 0,
            },
            {
                'pin_pulse': 17,
                'pin_dir': 16,
                'pin_limit_n': 50,
                'pin_limit_p': 51,
                'microstep': 2500,
                'course': 30000,
                'homing_delay': 200,
                'home_retract': 400,
                'has_encoder': True,
                'encoder_no': 1,
            },
        ]
    }

    def __init__(self, name, ip, arduino_id):
        self.arduino_id = arduino_id
        super(Robot, self).__init__(name, ip)


ROBOT_1_IP = '192.168.44.100'
ROBOTS = [
    Robot('Robot 1', ROBOT_1_IP, 0),
    Robot('Robot 2', ROBOT_1_IP, 1),
]
