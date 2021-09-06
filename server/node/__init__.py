from .station import Station
from .robot import Robot
from .rail import Rail
from .feeder import Feeder


ALL_NODES = [
    Robot('Robot 1', '192.168.44.100', arduino_id=0),
    Robot('Robot 2', '192.168.44.100', arduino_id=1),
    Rail('Rail', '192.168.44.100', arduino_id=2),

    Station('Station 1', '192.168.44.101'),
    Station('Station 2', '192.168.44.102'),
    Station('Station 3', '192.168.44.103'),
    Station('Station 4', '192.168.44.104'),
    Station('Station 5', '192.168.44.105'),
    Station('Station 6', '192.168.44.106'),
    Station('Station 7', '192.168.44.107'),
    Station('Station 8', '192.168.44.108'),
    Station('Station 9', '192.168.44.109'),
    Station('Station 10', '192.168.44.110'),
    Feeder('Feeder 1', '192.168.44.21'),

]
ALL_NODES_DICT = {n.name: n for n in ALL_NODES}

assert len(ALL_NODES_DICT) == len(ALL_NODES)

if 'Station 1' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 1']
    ALL_NODES_DICT['Station 1'].hw_config['H_ALIGNING'] = 230
    ALL_NODES_DICT['Station 1'].hw_config['H_PUSH'] = 238
    ALL_NODES_DICT['Station 1'].hw_config['H_PRE_DANCE'] = 244.5
    # ALL_NODES_DICT['Station 1'].hw_config['dosing_offset'] = -2

if 'Station 2' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 2']
    ALL_NODES_DICT['Station 2'].hw_config['H_ALIGNING'] = 225
    ALL_NODES_DICT['Station 2'].hw_config['H_PUSH'] = 237
    station.hw_config['H_PRE_DANCE'] = 244
    # station.hw_config['dosing_offset'] = 0
    station.hw_config['holder_webcam_direction'] = 'down'

if 'Station 3' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 3']
    station.hw_config['H_ALIGNING'] = 226
    station.hw_config['H_PUSH'] = 237
    station.hw_config['H_PRE_DANCE'] = 244

if 'Station 4' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 4']
    station.hw_config['H_ALIGNING'] = 226
    station.hw_config['H_PUSH'] = 238.5
    station.hw_config['H_PRE_DANCE'] = 245
    # station.hw_config['dosing_offset'] = -2
    station.hw_config['holder_webcam_direction'] = 'down'

if 'Station 5' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 5']
    station.hw_config['H_ALIGNING'] = 224
    station.hw_config['H_PUSH'] = 242
    station.hw_config['H_PRE_DANCE'] = 244

if 'Station 6' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 6']
    station.hw_config['H_ALIGNING'] = 227
    station.hw_config['H_PUSH'] = 240
    station.hw_config['H_PRE_DANCE'] = 248
    station.hw_config['holder_webcam_direction'] = 'down'


if 'Station 7' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 7']
    assert station.g2core_config[7][0] == 'z'
    station.g2core_config[7][1]['hi'] = 4
    station.hw_config['H_ALIGNING'] = 227
    station.hw_config['H_PUSH'] = 239.5
    station.hw_config['H_PRE_DANCE'] = 248


if 'Station 8' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 8']
    assert station.g2core_config[7][0] == 'z'
    station.g2core_config[7][1]['hi'] = 4
    station.hw_config['H_ALIGNING'] = 224
    station.hw_config['H_PUSH'] = 236
    station.hw_config['H_PRE_DANCE'] = 243.5
    station.hw_config['holder_webcam_direction'] = 'down'

if 'Station 9' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 9']
    station.hw_config['H_ALIGNING'] = 220
    station.hw_config['H_PUSH'] = 232.5
    station.hw_config['H_PRE_DANCE'] = 240


if 'Station 10' in ALL_NODES_DICT:
    station = ALL_NODES_DICT['Station 10']
    station.hw_config['H_ALIGNING'] = 223
    station.hw_config['H_PUSH'] = 234.5
    station.hw_config['H_PRE_DANCE'] = 242
    station.hw_config['holder_webcam_direction'] = 'down'

for i in range(0, 10):
    station_id = 'Station %d' % (i + 1)
    robot_id = 'Robot %d' % (int(i / 5) + 1)
    robot_slot = i % 5
    if (station_id in ALL_NODES_DICT) and (robot_id in ALL_NODES_DICT):
        ALL_NODES_DICT[station_id].set_robot(ALL_NODES_DICT[robot_id])
        ALL_NODES_DICT[robot_id].add_station(
            ALL_NODES_DICT[station_id], (i % 5))
