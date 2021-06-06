import asyncio

D_STANDBY = 40000
X_PARK = 0
Y_PARK = 3000
D_MIN = 20000
D_MAX = 24000
T_RAIL_FIXED_JACK = 0.7
T_RAIL_MOVING_JACK = 0.7
# Grab
X_GRAB_IN = 22750
Y_GRAB_IN_UP_1 = 6250
Y_GRAB_IN_DOWN = 0
Y_GRAB_IN_UP_2 = Y_GRAB_IN_UP_1
T_GRAB_IN = .5

# Place In
X_PLACE_IN = 29850
Y_PLACE_IN = 1600
Y_PLACE_IN_PRESS = 400
Y_PLACE_IN_COMEOUT = Y_PLACE_IN
T_PLACE_IN_FALL = 0.5
T_PLACE_IN_JACK_CLOSE = 0.5
T_PLACE_IN_PRESS = 0.2

# Start Station Process
X_MOVE_SAFE_STATION = 23000
Y_MOVE_SAFE_STATION = Y_GRAB_IN_UP_1
T_DOSING_PUSH = 0.5
T_DOSING_DANCE_UP_PRE = 0.3
T_PRESS_PRE = 0.3
T_PRESS = 1
T_PRESS_POST = 0.3
T_DOSING_DANCE_DOWN_PRE = 0.3
T_DOSING_DANCE_DOWN_POST = 0.3

# Deliver
H_DELIVER = 4000
X_DELIVER = X_PLACE_IN
Y_DELIVER = 8350
H_CLEAR = 2000
T_DELIVER_PRE = 0.2
T_DELIVER_POST = 0.2

# Capping
X_CAPPING = 4100
Y_CAPPING_DOWN_1 = 1750
Y_CAPPING_DOWN_2 = 0
Y_CAPPING_UP = Y_GRAB_IN_UP_1


async def main(system, ALL_NODES_DICT):
    await asyncio.sleep(1)

    robot_1 = ALL_NODES_DICT['Robot 1']
    stations = [ALL_NODES_DICT['Station %d' % (i + 1)] for i in range(5)]
    rail = ALL_NODES_DICT['Rail']
    all_nodes = stations + [robot_1, rail]
    for node in all_nodes:
        while not node.ready_for_command():
            await asyncio.sleep(.01)

    input('start?')
    print('Home Everything')
    print('Home Everything - 0- valves')
    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [0] * 5}))
    await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10}, assert_success=True)
    await rail.send_command({'verb': 'set_valves', 'valves': [0] * 2}, assert_success=True)

    print('Home Everything - 1- stations')
    await run_stations(stations, lambda s: s.send_command({'verb': 'home', 'axis': 3}, assert_success=True))

    print('Home Everything - 2- robot')
    await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10}, assert_success=True)
    await robot_1.move_all_the_way_up()

    await robot_1.send_command({'verb': 'home', 'axis': 1}, assert_success=True)
    await robot_1.send_command({'verb': 'home', 'axis': 0}, assert_success=True)

    print('Home Everything - 3- rail')
    await rail.send_command({'verb': 'home', 'axis': 0}, assert_success=True)
    await rail.goto(D_STANDBY)

    while True:
        print('start of loop')
        await rail.is_homed()

        input('start of while?')
        print('lets go grab input')
        await robot_1.goto(y=Y_GRAB_IN_UP_1)
        await robot_1.goto(x=X_GRAB_IN)
        await robot_1.goto(y=Y_GRAB_IN_DOWN)

        await robot_1.send_command(
            {'verb': 'set_valves', 'valves': [1] * 10})
        await asyncio.sleep(T_GRAB_IN)

        await robot_1.goto(y=Y_GRAB_IN_UP_2)

        print('put input into station')
        tasks = []
        for station in stations:
            tasks.append(station.send_command(
                {'verb': 'set_valves', 'valves': [0, 0, 0, 1]}, assert_success=True))

        tasks.append(robot_1.goto(x=X_PLACE_IN))
        await asyncio.gather(*tasks)

        await robot_1.goto(y=Y_PLACE_IN)
        await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10})
        await asyncio.sleep(T_PLACE_IN_FALL)

        print('press holder in')
        await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 5 + [1] * 5})
        await asyncio.sleep(T_PLACE_IN_JACK_CLOSE)
        await robot_1.goto(y=Y_PLACE_IN_PRESS)
        await asyncio.sleep(T_PLACE_IN_PRESS)
        await robot_1.goto(y=Y_PLACE_IN_COMEOUT)
        await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10})

        print('Move back for station to work')
        await robot_1.goto(x=X_MOVE_SAFE_STATION)

        await asyncio.gather(
            do_station(stations, robot_1, rail, all_nodes),
            do_rail(stations, robot_1, rail, all_nodes)
        )
        input('continue?')

        print('deliver')
        await run_stations(stations, lambda s: s.goto(H_DELIVER))
        await robot_1.goto(y=Y_DELIVER)
        await robot_1.goto(x=X_DELIVER)
        await robot_1.send_command({'verb': 'set_valves', 'valves': [1] * 5})
        await asyncio.sleep(T_DELIVER_PRE)
        await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [0]}))
        await asyncio.sleep(T_DELIVER_POST)
        await run_stations(stations, lambda s: s.goto(H_CLEAR))

        print('Capping')
        input('continue?')

        await robot_1.goto(x=X_CAPPING)
        await rail.send_command({'verb': 'set_valves', 'valves': [0, 1]})
        input('continue?')

        await asyncio.sleep(T_RAIL_MOVING_JACK)
        await rail.send_command({'verb': 'set_valves', 'valves': [1, 1]})
        input('continue?')

        await robot_1.goto(y=Y_CAPPING_DOWN_1)

        input('continue?')

        await rail.send_command({'verb': 'set_valves', 'valves': [0, 1]})
        input('continue?')

        await asyncio.sleep(T_RAIL_FIXED_JACK)
        await rail.send_command({'verb': 'set_valves', 'valves': [0, 0]})

        input('continue?')

        await robot_1.goto(y=Y_CAPPING_DOWN_2)
        await robot_1.send_command({'verb': 'set_valves', 'valves': [0] * 10})
        await robot_1.goto(y=Y_CAPPING_UP)
        print('end of loop')


async def do_station(stations, robot_1, rail, all_nodes):
    align_holders = []
    for station in stations:
        align_holders.append(station.send_command(
            {'verb': 'align', 'component': 'holder'}))
    align_holders = asyncio.gather(*align_holders)
    await align_holders

    print('prepare dosing')
    H_ALIGNING = 21500
    H_PUSH = 23000
    H_PUSH_BACK = H_PUSH - 500
    H_GRIPP = 23700

    await run_stations(stations, lambda s: s.goto('H_ALIGNING'))
    await run_stations(stations, lambda x: x.send_command({'verb': 'align', 'component': 'dosing'}))

    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [0, None, 0, 0]}))
    await run_stations(stations, lambda s: s.goto('H_ALIGNING', -500))
    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [1]}))
    await run_stations(stations, lambda s: s.goto('H_PUSH'))
    await asyncio.sleep(T_DOSING_PUSH)
    await run_stations(stations, lambda s: s.goto('H_PUSH', -500))
    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [0, None, 0, 1]}))
    await run_stations(stations, lambda s: s.goto('H_PUSH', 700))

    # dance
    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [1, None, 0, 1]}))
    await asyncio.sleep(T_DOSING_DANCE_UP_PRE)
    await run_stations(stations, lambda x: x.send_command_scenario({'verb': 'dance', 'value': 100}))
    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [0, 0, 0, 0, 1]}))

    print('press')
    await asyncio.sleep(T_PRESS_PRE)
    # TODO: verify microswitch
    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [0, 0, 1]}))
    await asyncio.sleep(T_PRESS)
    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [0, 0, 0]}))
    await asyncio.sleep(T_PRESS_POST)

    print('dance back')
    await run_stations(stations, lambda x: x.send_command({'verb': 'set_valves', 'valves': [1, 0, 0, 0, 0]}))
    await asyncio.sleep(T_DOSING_DANCE_DOWN_PRE)

    await run_stations(stations, lambda x: x.send_command_scenario({'verb': 'dance', 'value': -100, 'extra_m3': -100}))
    await asyncio.sleep(T_DOSING_DANCE_DOWN_POST)


async def do_rail(stations, robot_1, rail, all_nodes):
    await robot_1.goto(y=Y_MOVE_SAFE_STATION)
    await robot_1.goto(x=X_PARK)
    await robot_1.goto(y=Y_PARK)

    await rail.goto(D_MIN)

    await rail.send_command({'verb': 'set_valves', 'valves': [0, 1]})
    await asyncio.sleep(T_RAIL_MOVING_JACK)
    await rail.send_command({'verb': 'set_valves', 'valves': [1, 1]})
    await asyncio.sleep(T_RAIL_FIXED_JACK)

    await rail.goto(D_MAX)

    await rail.send_command({'verb': 'set_valves', 'valves': [0, 1]})
    await asyncio.sleep(T_RAIL_FIXED_JACK)
    await rail.send_command({'verb': 'set_valves', 'valves': [0, 0]})
    await asyncio.sleep(T_RAIL_MOVING_JACK)

    await rail.goto(D_STANDBY)


def run_stations(stations, func):
    tasks = []
    for station in stations:
        tasks.append(func(station))

    return asyncio.gather(*tasks)
