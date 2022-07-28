from .station import Station
from .robot import Robot
from .rail import Rail
from .feeder import Feeder
from .dosing import Dosing
from .demo import Demo


ALL_NODES = [
    Demo('demo', '192.168.31.44'),

    # Robot('Robot 1', '192.168.44.100', arduino_id=0),
    # Robot('Robot 2', '192.168.44.100', arduino_id=1),
    # Rail('Rail', '192.168.44.100', arduino_id=2),

    # Station('Station 1', '192.168.44.101'),
    # Station('Station 2', '192.168.44.102'),
    # Station('Station 3', '192.168.44.103'),
    # Station('Station 4', '192.168.44.104'),
    # Station('Station 5', '192.168.44.105'),
    # Station('Station 6', '192.168.44.106'),
    # Station('Station 7', '192.168.44.107'),
    # Station('Station 8', '192.168.44.108'),
    # Station('Station 9', '192.168.44.109'),
    # Station('Station 10', '192.168.44.110'),

    # Feeder('Feeder 1', '192.168.44.21', arduino_id=2),
    # Dosing('Dosing F. 1', '192.168.44.21', arduino_id=1),
]
ALL_NODES_DICT = {n.name: n for n in ALL_NODES}


def ip_to_node(ip):
    for node in ALL_NODES:
        if node.ip == ip:
            return node
    return None


assert len(ALL_NODES_DICT) == len(ALL_NODES)

if 'Station X' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station X']
    station.hw_config['H_ALIGNING'] = 235
    station.hw_config['H_PUSH'] = 246
    station.hw_config['H_PRE_DANCE'] = 254
    station.hw_config['dosing_offset'] = 0  # posetive moves to left
# X1 235,246,254
'''
    "101": {
        "dosing": {
            "bt61bl83": {
                "zero": 201
            }
        },
        "dosing_roi": {
            "dx": 250,
            "dy": 213,
            "x0": 140,
            "y0": 144
        },
        "holder": {
            "cmbm1h2t": {
                "zero": 211
            }
        },
        "holder_roi": {
            "dx": 188,
            "dy": 174,
            "x0": 214,
            "y0": 249
        }
    },
'''
# X2 235,246,254

if 'Station 1' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 1']
    station.hw_config['H_ALIGNING'] = 230
    station.hw_config['H_PUSH'] = 238
    station.hw_config['H_PRE_DANCE'] = 245

if 'Station 2' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 2']
    station.hw_config['H_ALIGNING'] = 240
    station.hw_config['H_PUSH'] = 250
    station.hw_config['H_PRE_DANCE'] = 258.5
    station.hw_config['presence_threshold']['holder'] = 65

if 'Station 3' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 3']
    station.hw_config['H_ALIGNING'] = 226
    station.hw_config['H_PUSH'] = 237
    station.hw_config['H_PRE_DANCE'] = 244
    station.hw_config['dosing_webcam_direction'] = 'riu'

if 'Station 4' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 4']
    station.hw_config['H_ALIGNING'] = 226
    station.hw_config['H_PUSH'] = 238.5
    station.hw_config['H_PRE_DANCE'] = 246
    station.hw_config['holder_webcam_direction'] = 'down'

if 'Station 5' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 5']
    station.hw_config['H_ALIGNING'] = 224
    station.hw_config['H_PUSH'] = 242
    station.hw_config['H_PRE_DANCE'] = 246

if 'Station 6' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 6']
    station.hw_config['H_ALIGNING'] = 227
    station.hw_config['H_PUSH'] = 240
    station.hw_config['H_PRE_DANCE'] = 248
    station.hw_config['dosing_webcam_direction'] = 'riu'
    station.hw_config['presence_threshold']['holder'] = 63
    # station.hw_config['dosing_offset'] = 1  # posetive moves to left

    # station.hw_config['cameras']['dosing']['rois']['sit_right']['x0'] = 50


if 'Station 7' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 7']
    Z_CONFIG_INDEX = 5
    assert station.g2core_config[Z_CONFIG_INDEX][0] == 'z'
    station.g2core_config[Z_CONFIG_INDEX][1]['hi'] = 4
    station.hw_config['H_ALIGNING'] = 228
    station.hw_config['H_PUSH'] = 240
    station.hw_config['H_PRE_DANCE'] = 248
    # station.hw_config['holder_offset'] = 1  # posetive moves to right


if 'Station 8' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 8']
    station.hw_config['H_ALIGNING'] = 235
    station.hw_config['H_PUSH'] = 246
    station.hw_config['H_PRE_DANCE'] = 254
    station.hw_config['dosing_webcam_direction'] = 'riu'


if 'Station 9' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 9']
    station.hw_config['H_ALIGNING'] = 228
    station.hw_config['H_PUSH'] = 238
    station.hw_config['H_PRE_DANCE'] = 246
    station.hw_config['dosing_webcam_direction'] = 'riu'
    station.hw_config['holder_existance_y_margin'] = 17
    station.hw_config['dosing_offset'] = -1  # posetive moves to right

if 'Station 10' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 10']
    station.hw_config['H_ALIGNING'] = 226
    station.hw_config['H_PUSH'] = 235.5
    station.hw_config['H_PRE_DANCE'] = 243
    station.hw_config['holder_webcam_direction'] = 'down'
    # station.hw_config['dosing_offset'] = 1

if 'Robot 1' in ALL_NODES_DICT:
    robot = ALL_NODES_DICT['Robot 1']
    robot.hw_config['X_CAPPING'] = 52.5
    robot.hw_config['X_GRAB_IN'] = 286
    robot.hw_config['X_INPUT'] = 374.5

if 'Robot 2' in ALL_NODES_DICT:
    robot = ALL_NODES_DICT['Robot 2']
    robot.hw_config['Y_GRAB_IN_UP_2'] = 62
    robot.hw_config['X_CAPPING'] = 57


for i in range(0, 10):
    station_id = 'Station %d' % (i + 1)
    robot_id = 'Robot %d' % (int(i / 5) + 1)
    robot_slot = i % 5
    if (station_id in ALL_NODES_DICT) and (robot_id in ALL_NODES_DICT):
        ALL_NODES_DICT[station_id].set_robot(ALL_NODES_DICT[robot_id])
        ALL_NODES_DICT[robot_id].add_station(
            ALL_NODES_DICT[station_id], (i % 5))
