import asyncio


N = 5
SPEED = 1  # between 0-1
SERVICE_FUNC_NO_FEEDER = 0
SERVICE_FUNC_NO_CARTRIDGE = 0
''' Station '''
FEED_Z_UP = 10000 * SPEED
FEED_Z_DOWN = 15000 * SPEED
FEED_DANCE = 40000

# Vision
ALIGN_SPEED_DOSING = 25000
ALIGN_SPEED_HOLDER = 25000

''' Robot '''
FEED_X = 50000 * SPEED
FEED_Y_UP = 5000 * SPEED
FEED_Y_DOWN = 5000 * SPEED
FEED_Y_CAPPING = 1000 * SPEED
FEED_Y_PRESS = 3000 * SPEED

# Park
X_PARK = 10
Y_PARK = 40

# Capping
X_CAPPING = 51.25
Y_CAPPING_DOWN_1 = 22
Y_CAPPING_DOWN_2 = 10
assert Y_CAPPING_DOWN_2 < Y_PARK


''' Rail '''
FEED_RAIL_FREE = 30000 * SPEED
FEED_RAIL_INTACT = 16000 * SPEED
D_STANDBY = 250
D_MIN = D_STANDBY - 25 * N
assert D_MIN >= 0
T_RAIL_JACK1 = 1.8
T_RAIL_JACK2 = 1.8
T_RAIL_FEEDER_JACK_PERCENTAGE = .2

''' Feeder '''
FEED_FEEDER_DELIVER = 50000 * SPEED
FEED_FEEDER_FEED = 100000 * SPEED
FEED_FEEDER_COMEBACK = 70000 * SPEED
FEEDER_Z_IDLE = 16
FEEDER_Z_DELIVER = 717
JERK_FEEDER_COMEBACK = 1300
JERK_FEEDER_FEED = 10000
JERK_FEEDER_IDLE = 2500


async def gather_all_nodes(system, ALL_NODES):
    stations = [node for node in ALL_NODES if node.name.startswith('Station ')]
    robots = [node for node in ALL_NODES if node.name.startswith('Robot ')]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]

    all_nodes = stations + robots + [rail, feeder]

    # All Nodes Ready?
    for node in all_nodes:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    return all_nodes, feeder, rail, robots, stations


def check_home_all_nodes(system, feeder, rail, robots, stations):
    assert feeder.is_at_loc(
        z=FEEDER_Z_IDLE) or feeder.is_at_loc(z=FEEDER_Z_DELIVER)
    assert rail.is_at_loc(z=D_STANDBY)

    # robots
    for robot in robots:
        condition = robot.is_at_loc(
            x=0, y=0) or robot.is_at_loc(x=X_PARK, y=Y_PARK)
        message = '%s is not at proper location' % robot.name
        assert condition, message

    # stations
    for station in stations:
        condition = station.is_at_loc(z=0.5) or station.is_at_loc(
            z=50) or station.is_at_loc(z=0)
        message = '%s is not at proper location' % station.name
        assert condition, message
