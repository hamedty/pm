from .node import Node


class Robot(Node):
    type = 'robot'
    arduino_reset_pin = 2
    valves = [15, 16]
    hw_config = {
        'valves': [37, 39],
        'motors': [
            {
                'pin_pulse': 12,
                'pin_dir': 11,
                'pin_limit_n': 15,
                'pin_limit_p': 16,
                'microstep': 2500,
                'course': 10000,
                'homing_delay': 200,
                'home_retract': 400,
            },
            {
                'pin_pulse': 9,
                'pin_dir': 8,
                'pin_limit_n': 14,
                'microstep': 2500,
                'course': 30000,
                'homing_delay': 200,
                'home_retract': 400,
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
