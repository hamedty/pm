from .robot import Robot
from .robot import ROBOT_1_IP


class Rail(Robot):
    type = 'rail'


RAILS = [
    Robot('Rail 1', ROBOT_1_IP, 2),
]
