from .station import Station
from .robot import Robot
from .rail import Rail


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
    # Station('Station 8', '192.168.44.108'),
    Station('Station 9', '192.168.44.109'),
    Station('Station 10', '192.168.44.110'),

]
ALL_NODES_DICT = {n.name: n for n in ALL_NODES}

assert len(ALL_NODES_DICT) == len(ALL_NODES)

ALL_NODES_DICT['Station 1'].hw_config['H_ALIGNING'] = 230
ALL_NODES_DICT['Station 1'].hw_config['H_PUSH'] = 238
ALL_NODES_DICT['Station 1'].hw_config['H_PRE_DANCE'] = 244.5
ALL_NODES_DICT['Station 1'].hw_config['dosing_offset'] = -2

ALL_NODES_DICT['Station 2'].hw_config['H_ALIGNING'] = 225
ALL_NODES_DICT['Station 2'].hw_config['H_PUSH'] = 237
ALL_NODES_DICT['Station 2'].hw_config['H_PRE_DANCE'] = 244
ALL_NODES_DICT['Station 2'].hw_config['dosing_offset'] = -2
ALL_NODES_DICT['Station 2'].hw_config['holder_webcam_direction'] = 'down'

ALL_NODES_DICT['Station 3'].hw_config['H_ALIGNING'] = 226
ALL_NODES_DICT['Station 3'].hw_config['H_PUSH'] = 237
ALL_NODES_DICT['Station 3'].hw_config['H_PRE_DANCE'] = 244

ALL_NODES_DICT['Station 4'].hw_config['H_ALIGNING'] = 226
ALL_NODES_DICT['Station 4'].hw_config['H_PUSH'] = 238.5
ALL_NODES_DICT['Station 4'].hw_config['H_PRE_DANCE'] = 245
ALL_NODES_DICT['Station 4'].hw_config['dosing_offset'] = -2
ALL_NODES_DICT['Station 4'].hw_config['holder_webcam_direction'] = 'down'

ALL_NODES_DICT['Station 5'].hw_config['H_ALIGNING'] = 224
ALL_NODES_DICT['Station 5'].hw_config['H_PUSH'] = 242
ALL_NODES_DICT['Station 5'].hw_config['H_PRE_DANCE'] = 244


for i in range(0, 10):
    station_id = 'Station %d' % (i + 1)
    robot_id = 'Robot %d' % ((i % 5) + 1)
    if (station_id in ALL_NODES_DICT) and (robot_id in ALL_NODES_DICT):
        ALL_NODES_DICT[station_id].set_robot(ALL_NODES_DICT[robot_id])
        ALL_NODES_DICT[robot_id].add_station(ALL_NODES_DICT[station_id])
