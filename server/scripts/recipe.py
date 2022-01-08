import asyncio


N = 10
SPEED = 1  # between 0-1
SERVICE_FUNC_NO_FEEDER = 1
SERVICE_FUNC_NO_CARTRIDGE = 1
SERVICE_FUNC_NO_DOSING = 1
''' Station '''
FEED_Z_UP = 10000 * SPEED
FEED_Z_DOWN = 15000 * SPEED
FEED_DANCE = 40000
STATION_Z_OUTPUT = 70
STATION_Z_OUTPUT_SAFE = STATION_Z_OUTPUT - 30


# Vision
ALIGN_SPEED_DOSING = 25000
ALIGN_SPEED_HOLDER = 25000
VISION_RETRIES = [4, 4, 3, 3]

''' Robot '''
FEED_X = 30000 * SPEED * .5
FEED_Y_UP = 55000 * SPEED
FEED_Y_DOWN = 55000 * SPEED
FEED_Y_DOWN_CAP = 8000 * SPEED
FEED_Y_DOWN_PRESS = 5000 * SPEED

# Park
X_PARK = 10
Y_PARK = 40

# Capping
Y_CAPPING_DOWN = 10
assert Y_CAPPING_DOWN < Y_PARK


''' Rail '''
FEED_RAIL_FREE = 30000 * SPEED
FEED_RAIL_INTACT = 16000 * SPEED
JERK_RAIL_FREE = 2000
JERK_RAIL_INTACT = 4500

D_STANDBY = 250
D_MIN = -1  # D_STANDBY - 25 * N
assert D_MIN >= -5
T_RAIL_JACK1 = 1.5
T_RAIL_JACK2 = 1.2
T_RAIL_FEEDER_JACK = 0.5
assert T_RAIL_FEEDER_JACK < T_RAIL_JACK1

''' Feeder '''
FEED_FEEDER_FEED = 100000 * SPEED
FEED_FEEDER_DELIVER = 70000 * SPEED
FEED_FEEDER_COMEBACK = 50000 * SPEED  # maximiezed: 50000

JERK_FEEDER_FEED = 10000 * .5  # * .7
JERK_FEEDER_DELIVER = 2500 * .5  # * .7
# JERK_FEEDER_COMEBACK = never used - same as deliver

FEEDER_Z_IDLE = 16
FEEDER_Z_DELIVER = 717


async def gather_all_nodes(system, ALL_NODES, wait_for_readiness=True):
    stations = [node for node in ALL_NODES if node.name.startswith('Station ')]
    robots = [node for node in ALL_NODES if node.name.startswith('Robot ')]
    rail = [node for node in ALL_NODES if node.name.startswith('Rail')][0]
    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]
    dosing_feeder = [
        node for node in ALL_NODES if node.name.startswith('Dosing ')][0]

    all_nodes = stations + robots + [rail, feeder]

    # All Nodes Ready?
    if wait_for_readiness:
        for node in all_nodes:
            while not node.ready_for_command():
                await asyncio.sleep(.01)

    return all_nodes, feeder, dosing_feeder, rail, robots, stations


async def check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations):
    # G2Core Flag
    for node in all_nodes:
        # only checks if home squence has beed ran. location must be checked separately
        is_homed = await node.is_homed()
        assert is_homed, '%s is not homed!' % node.name

    # Feeder
    assert feeder.is_at_loc(
        z=FEEDER_Z_IDLE) or feeder.is_at_loc(z=FEEDER_Z_DELIVER)
    assert await feeder.read_metric('out2') == 0, "Feeder Jack is out - transfer first"

    # Rail
    assert rail.is_at_loc(z=D_STANDBY)

    # robots
    for robot in robots:
        condition = robot.is_at_loc(
            x=0, y=0) or robot.is_at_loc(x=X_PARK, y=Y_PARK)
        message = '%s is not at proper location' % robot.name
        assert condition, message

    # stations
    for station in stations:
        condition = station.is_at_loc(z=-1) or station.is_at_loc(
            z=40) or station.is_at_loc(z=0)
        message = '%s is not at proper location' % station.name
        assert condition, message
