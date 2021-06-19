import time
import asyncio
from .recipe import *

# do_stations, do_rail_n_robots
#               do_robots_cap
#               do_rail
#               do_robots_pickup
# do_exchange


async def main(system, ALL_NODES):
    all_nodes, rail, robot_1, stations = await gather_all_nodes(system, ALL_NODES)

    print('Home Everything')
    await home_all_nodes(all_nodes, rail, robot_1, stations)

    STATUS = {
        'stations_full': False,
        'robots_full': False,
    }

    while True:
        input('repeat?')
        t0 = time.time()
        await asyncio.gather(
            do_stations(stations, robot_1, rail, all_nodes,
                        STATUS, standalone=True),
            # do_rail_n_robots(stations, robot_1, rail, all_nodes, STATUS)
        )
        print('rail and robot:', time.time() - t0)
        t0 = time.time()
        # await do_exchange(stations, robot_1, rail, all_nodes, STATUS)
        print('exchange:', time.time() - t0)


async def gather_all_nodes(system, ALL_NODES):
    stations = [node for node in ALL_NODES if node.name.startswith('Station ')]
    robots = [node for node in ALL_NODES if node.name.startswith('Robot ')]
    robot_1 = robots[0]
    rails = [node for node in ALL_NODES if node.name.startswith('Rail')]
    rail = rails[0]

    all_nodes = stations + [robot_1, rail]

    # All Nodes Ready?
    for node in all_nodes:
        while not node.ready_for_command():
            await asyncio.sleep(.01)
    return all_nodes, rail, robot_1, stations


async def home_all_nodes(all_nodes, rail, robot_1, stations):
    await run_stations(stations, lambda x: x.set_valves([0] * 3))
    # await run_stations(stations, lambda x: x.set_valves([0] * 5))
    # input('go?')
    await robot_1.set_valves([0] * 10)
    await rail.set_valves([0] * 2)

    await run_stations(stations, lambda s: s.home())
    await run_stations(stations, lambda x: x.set_valves([0, 0, 0, 1, 0, 0]))
    # await robot_1.home()
    # await rail.home()
    # await rail.goto(D_STANDBY, feed=FEED_RAIL_FREE * .6)


async def do_rail_n_robots(stations, robot_1, rail, all_nodes, STATUS):
    t0 = time.time()
    await do_robots_cap(stations, robot_1, rail, all_nodes, STATUS)
    print('do_robots_cap:', time.time() - t0)

    t0 = time.time()
    await do_rail(stations, robot_1, rail, all_nodes, STATUS)
    print('do_rail:', time.time() - t0)

    t0 = time.time()
    await do_robots_pickup(stations, robot_1, rail, all_nodes, STATUS)
    print('do_robots_pickup:', time.time() - t0)


async def do_exchange(stations, robot_1, rail, all_nodes, STATUS):
    print('deliver')

    data = {}
    data['X_INPUT'] = 375
    data['Y_INPUT_DOWN_1'] = 35
    data['Y_INPUT_UP'] = 55
    data['Y_INPUT_DOWN_3'] = 10
    data['Y_INPUT_DOWN_2'] = data['Y_INPUT_DOWN_3'] + 10

    data['FEED_X'] = FEED_X
    data['FEED_Y_UP'] = FEED_Y_UP
    data['FEED_Y_DOWN'] = FEED_Y_DOWN
    data['FEED_Y_PRESS'] = 3000

    data['T_INPUT_RELEASE'] = 0.5
    data['T_HOLDER_JACK_CLOSE'] = 0.5
    data['T_PRE_PRESS'] = 0.2
    data['T_POST_PRESS'] = 0.2

    c = '''
    G1 X%(X_INPUT).2f F%(FEED_X)d
    G1 Y%(Y_INPUT_DOWN_1).2f F%(FEED_Y_DOWN)d
    M100 ({out1: 0, out2: 0, out3: 0, out4: 0, out5: 0})
    M100 ({out6: 0, out7: 0, out8: 0, out9: 0, out10: 0})
    G4 P%(T_INPUT_RELEASE).2f
    ''' % data
    await robot_1.send_command_raw(c)

    c_robot = '''
    G1 Y%(Y_INPUT_UP).2f F%(FEED_Y_UP)d
    M100 ({out6: 1, out7: 1, out8: 1, out9: 1, out10: 1})
    G4 P%(T_HOLDER_JACK_CLOSE).2f
    G1 Y%(Y_INPUT_DOWN_2).2f F%(FEED_Y_DOWN)d
    G4 P%(T_PRE_PRESS).2f
    G1 Y%(Y_INPUT_DOWN_3).2f F%(FEED_Y_PRESS)d
    G4 P%(T_POST_PRESS).2f
    ''' % data

    data = {}
    data['Z_OUTPUT'] = 80
    data['FEED_Z_DOWN'] = FEED_Z_DOWN / 4.0

    c_station = '''
    G1 Z%(Z_OUTPUT).2f F%(FEED_Z_DOWN)d
    ''' % data
    await asyncio.gather(
        robot_1.send_command_raw(c_robot),
        run_stations(stations, lambda x: x.send_command_raw(c_station)),
    )

    data['Y_OUTPUT'] = 70
    data['Z_OUTPUT_SAFE'] = data['Z_OUTPUT'] - 20
    data['X_OUTPUT_SAFE'] = X_CAPPING

    data['T_OUTPUT_GRIPP'] = 0.1
    data['T_OUTPUT_RELEASE'] = 0.2

    data['FEED_X'] = FEED_X
    data['FEED_Y_UP'] = FEED_Y_UP
    data['FEED_Z_DOWN'] = FEED_Z_DOWN
    data['FEED_Z_UP'] = FEED_Z_UP

    c = '''
    G1 Y%(Y_OUTPUT).2f F%(FEED_Y_UP)d
    M100 ({out1: 1, out2: 1, out3: 1, out4: 1, out5: 1})
    ''' % data
    await robot_1.send_command_raw(c)

    await asyncio.sleep(data['T_OUTPUT_GRIPP'])

    c = '''
    M100 ({out1: 0, out2: 1})
    G4 P%(T_OUTPUT_RELEASE).2f
    G1 Z%(Z_OUTPUT_SAFE).2f F%(FEED_Z_UP)d
    ''' % data
    await run_stations(stations, lambda x: x.send_command_raw(c))

    # Start Align Holder
    create_station_holder_align_task(
        stations, robot_1, rail, all_nodes, STATUS)

    c = '''
    G1 X%(X_OUTPUT_SAFE).2f F%(FEED_X)d
    ''' % data
    await robot_1.send_command_raw(c)
    # STATUS['robots_full'] = False
    STATUS['stations_full'] = True


ALIGN_HOLDER_TASK = None


def create_station_holder_align_task(stations, robot_1, rail, all_nodes, STATUS):
    global ALIGN_HOLDER_TASK
    align_holders = []
    for station in stations:
        align_holders.append(station.send_command(
            {'verb': 'align', 'component': 'holder', 'speed': ALIGN_SPEED_HOLDER}))
    ALIGN_HOLDER_TASK = asyncio.gather(*align_holders)


async def do_stations(stations, robot_1, rail, all_nodes, STATUS, standalone):
    if (not STATUS['stations_full']) and (not standalone):
        return

    if standalone:
        await run_stations(stations, lambda x: x.set_valves([0, 1]))
        create_station_holder_align_task(
            stations, robot_1, rail, all_nodes, STATUS)
    global ALIGN_HOLDER_TASK
    await ALIGN_HOLDER_TASK

    print('prepare dosing')
    tasks = []
    for station in stations:
        tasks.append(do_station(station, STATUS))
    await asyncio.gather(*tasks)

    if standalone:
        await run_stations(stations, lambda x: x.set_valves([0]))


async def do_station(station, STATUS):
    t0 = time.time()

    data = {}
    # go to aliging location
    data['H_ALIGNING'] = station.hw_config['H_ALIGNING']
    data['FEED_ALIGNING'] = FEED_Z_DOWN

    # Fall
    data['PAUSE_FALL_DOSING'] = 0.05

    # Ready to push
    data['H_READY_TO_PUSH'] = data['H_ALIGNING'] - 8
    data['FEED_READY_TO_PUSH'] = FEED_Z_UP
    data['PAUSE_READY_TO_PUSH'] = 0.05

    # Push
    data['H_PUSH'] = station.hw_config['H_PUSH']
    data['FEED_PUSH'] = FEED_Z_DOWN / 3.0
    data['PAUSE_PUSH'] = 0.1
    data['H_PUSH_BACK'] = data['H_PUSH'] - 5
    data['FEED_PUSH_BACK'] = FEED_Z_UP

    # Dance
    data['PAUSE_JACK_PRE_DANCE_1'] = 0.05
    data['PAUSE_JACK_PRE_DANCE_2'] = 0.05
    data['PAUSE_JACK_PRE_DANCE_3'] = 0.05
    data['H_PRE_DANCE'] = station.hw_config['H_PRE_DANCE']
    data['FEED_PRE_DANCE'] = FEED_Z_UP

    dance_rev = 1
    data['H_DANCE'] = data['H_PRE_DANCE'] - (11 * dance_rev)
    data['Y_DANCE'] = 360 * dance_rev
    data['FEED_DANCE'] = FEED_DANCE

    # Press
    data['PAUSE_PRESS0'] = 0.1
    data['PAUSE_PRESS1'] = 0.3
    data['PAUSE_PRESS2'] = 0.5

    # Dance Back
    data['PAUSE_JACK_PRE_DANCE_BACK'] = .2
    data['PAUSE_POST_DANCE_BACK'] = .3

    dance_back_rev = -1.1
    data['H_DANCE_BACK'] = data['H_DANCE'] - (11 * dance_back_rev)
    data['Y_DANCE_BACK'] = data['Y_DANCE'] + 360 * dance_back_rev
    data['FEED_DANCE_BACK'] = data['FEED_DANCE']

    # Deliver
    data['H_DELIVER'] = 1
    data['FEED_DELIVER'] = FEED_Z_UP

    c = '''
; go to aligning position
G1 Z%(H_ALIGNING).2f F%(FEED_ALIGNING)d
M100 ({out1: 1})
''' % data

    await station.send_command_raw(c)
    print('aligning 1', station.ip, time.time() - t0)
    t0 = time.time()

    await station.send_command({'verb': 'align', 'component': 'dosing', 'speed': ALIGN_SPEED_DOSING})
    print('aligning 2', station.ip, time.time() - t0)
    t0 = time.time()

    c = '''
; release dosing
M100 ({out1: 0, out4: 0})
G4 P%(PAUSE_FALL_DOSING).2f

; ready to push
G1 Z%(H_READY_TO_PUSH).2f F%(FEED_READY_TO_PUSH)d
M100 ({out1: 1})
G4 P%(PAUSE_READY_TO_PUSH).2f

; push and come back
G1 Z%(H_PUSH).2f F%(FEED_PUSH)d
G4 P%(PAUSE_PUSH).2f
G1 Z%(H_PUSH_BACK).2f F%(FEED_PUSH_BACK)d

; prepare for dance
M100 ({out1: 0, out4: 1})
G4 P%(PAUSE_JACK_PRE_DANCE_1).2f
G1 Z%(H_PRE_DANCE).2f F%(FEED_PRE_DANCE)d
G4 P%(PAUSE_JACK_PRE_DANCE_2).2f
M100 ({out1: 1})
G4 P%(PAUSE_JACK_PRE_DANCE_3).2f

; dance
G1 Z%(H_DANCE).2f Y%(Y_DANCE).2f F%(FEED_DANCE)d

; press
M100 ({out1: 0, out2: 0, out4: 0})
G4 P%(PAUSE_PRESS0).2f
M100 ({out5: 1})
G4 P%(PAUSE_PRESS1).2f
M100 ({out3: 1})
G4 P%(PAUSE_PRESS2).2f
M100 ({out3: 0})

; dance back
M100 ({out1: 1, out4: 1, out5: 0})
G4 P%(PAUSE_JACK_PRE_DANCE_BACK).2f
G1 Z%(H_DANCE_BACK).2f Y%(Y_DANCE_BACK).2f F%(FEED_DANCE_BACK)d
M100 ({out4: 0})
G4 P%(PAUSE_POST_DANCE_BACK).2f

; deliver
G1 Z%(H_DELIVER).2f F%(FEED_DELIVER)d
M100 ({out4: 1})
''' % data

    await station.send_command_raw(c)
    print('aligning 3', station.ip, time.time() - t0)


async def do_robots_cap(stations, robot_1, rail, all_nodes, STATUS):
    if not STATUS['stations_full']:
        return

    print('Capping')

    async def swap_rail_jacks_1(rail):
        await rail.set_valves([1, 0])
        await asyncio.sleep(T_RAIL_MOVING_JACK)
        await rail.set_valves([1, 1])

    async def swap_rail_jacks_2(rail):
        await rail.set_valves([1, 0])
        await asyncio.sleep(T_RAIL_FIXED_JACK)
        await rail.set_valves([0, 0])

    await asyncio.gather(
        swap_rail_jacks_1(rail),
        robot_1.goto(x=X_CAPPING, feed=FEED_X),
    )

    await robot_1.goto(y=Y_CAPPING_DOWN_1, feed=FEED_Y_DOWN)

    await asyncio.gather(
        swap_rail_jacks_2(rail),
        robot_1.goto(y=Y_CAPPING_DOWN_2, feed=FEED_Y_CAPPING),
    )

    await robot_1.set_valves([0] * 10)

    await robot_1.goto(x=X_PARK, feed=FEED_X)


async def do_robots_pickup(stations, robot_1, rail, all_nodes, STATUS):
    print('lets go grab input')

    data = {}
    data['Y_GRAB_IN_UP_1'] = 65
    data['X_GRAB_IN'] = 284.5
    data['Y_GRAB_IN_DOWN'] = 0
    data['Y_GRAB_IN_UP_2'] = data['Y_GRAB_IN_UP_1']

    data['FEED_Y_UP'] = FEED_Y_UP
    data['FEED_Y_DOWN'] = FEED_Y_DOWN
    data['FEED_X'] = FEED_X

    data['T_GRAB_IN'] = 0.5

    c = '''
G1 Y%(Y_GRAB_IN_UP_1).2f F%(FEED_Y_UP)d
G1 X%(X_GRAB_IN).2f F%(FEED_X)d
G1 Y%(Y_GRAB_IN_DOWN).2f F%(FEED_Y_DOWN)d

M100 ({out1: 1, out2: 1, out3: 1, out4: 1, out5: 1})
M100 ({out6: 1, out7: 1, out8: 1, out9: 1, out10: 1})
G4 P%(T_GRAB_IN).2f

G1 Y%(Y_GRAB_IN_UP_2).2f F%(FEED_Y_UP)d
''' % data
    await robot_1.send_command_raw(c)

    STATUS['robots_full'] = True


async def do_rail(stations, robot_1, rail, all_nodes, STATUS):
    task2 = asyncio.create_task(robot_1.goto(y=Y_PARK, feed=FEED_Y_UP / 5.0))

    data = {}
    data['D_STANDBY'] = D_STANDBY
    data['D_MIN'] = data['D_STANDBY'] - 125
    data['D_MAX'] = data['D_MIN']  # + 25 * 10

    data['FEED_RAIL_FREE'] = FEED_RAIL_FREE
    data['FEED_RAIL_INTACT'] = FEED_RAIL_INTACT
    data['T_RAIL_JACK1'] = .4
    data['T_RAIL_JACK2'] = .7

    c = '''
; rail backward
G1 Z%(D_MIN).2f F%(FEED_RAIL_FREE)d

; change jacks to moving
M100 ({out9: 1, out10: 0})
G4 P%(T_RAIL_JACK1).2f
M100 ({out9: 1, out10: 1})
G4 P%(T_RAIL_JACK2).2f

; rail forward
G1 Z%(D_MAX).2f F%(FEED_RAIL_INTACT)d

; change jacks to moving
M100 ({out9: 1, out10: 0})
G4 P%(T_RAIL_JACK1).2f
M100 ({out9: 0, out10: 0})
G4 P%(T_RAIL_JACK2).2f

; rail park
G1 Z%(D_STANDBY).2f F%(FEED_RAIL_FREE)d
''' % data
    await rail.send_command_raw(c)
    await task2


def run_stations(stations, func):
    tasks = []
    for station in stations:
        tasks.append(func(station))

    return asyncio.gather(*tasks)
