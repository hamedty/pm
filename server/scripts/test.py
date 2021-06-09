import asyncio


# Grab
X_GRAB_IN = 285
Y_GRAB_IN_UP_1 = 78
Y_GRAB_IN_DOWN = 0
Y_GRAB_IN_UP_2 = Y_GRAB_IN_UP_1
T_GRAB_IN = .5


# D_STANDBY = 40000
X_PARK = 0
Y_PARK = 3000
# D_MIN = 20000
# D_MAX = 24000
T_RAIL_FIXED_JACK = 0.7
T_RAIL_MOVING_JACK = 0.7
# Grab
X_GRAB_IN = 284.5
Y_GRAB_IN_UP_1 = 78
Y_GRAB_IN_DOWN = 0
Y_GRAB_IN_UP_2 = Y_GRAB_IN_UP_1
T_GRAB_IN = .5

# Place In
X_PLACE_IN = 373
Y_PLACE_IN = 20
Y_PLACE_IN_PRESS = 5
Y_PLACE_IN_COMEOUT = Y_PLACE_IN
T_PLACE_IN_FALL = 0.5
T_PLACE_IN_JACK_CLOSE = 0.5
T_PLACE_IN_PRESS = 0.2

# Start Station Process
X_MOVE_SAFE_STATION = 287.5
Y_MOVE_SAFE_STATION = Y_GRAB_IN_UP_1
T_DOSING_PUSH = 0.5
T_DOSING_DANCE_UP_PRE = 0.3
T_PRESS_PRE = 0.3
T_PRESS = 1
T_PRESS_POST = 0.3
T_DOSING_DANCE_DOWN_PRE = 0.3
T_DOSING_DANCE_DOWN_POST = 0.3

# Deliver
# H_DELIVER = 4000
X_DELIVER = X_PLACE_IN
Y_DELIVER = 104.5
# H_CLEAR = 2000
T_DELIVER_PRE = 0.2
T_DELIVER_POST = 0.2

# Capping
X_CAPPING = 51.25
Y_CAPPING_DOWN_1 = 22
Y_CAPPING_DOWN_2 = 0
Y_CAPPING_UP = Y_GRAB_IN_UP_1


async def test(system, ALL_NODES_DICT):
    # station = ALL_NODES_DICT['Station 1']
    #
    # while not station.ready_for_command():
    #     await asyncio.sleep(.01)
    #
    # await station.set_valves([0] * 6)
    # await station.send_command_raw('G54')
    # print('salam')
    # # await station.home()
    # # await station.set_valves([1, 1])
    #
    # await station.send_command(
    #     {'verb': 'align', 'component': 'holder', 'speed': 25000})
    # await station.set_valves([1, 1])
    # await station.send_command(
    #     {'verb': 'align', 'component': 'holder', 'speed': 25000})

    robot_1 = ALL_NODES_DICT['Robot 1']

    # while not robot.ready_for_command():
    #     await asyncio.sleep(.01)

    print('salam')
    await asyncio.sleep(2)

    print('homing')
    await robot_1.set_valves([0] * 10)
    await robot_1.home()

    # while True:
    for i in range(1):
        # input('repeat?')
        # await rail.is_homed()
        print('lets go grab input')

        await robot_1.goto(y=Y_GRAB_IN_UP_1)
        await robot_1.goto(x=X_GRAB_IN)
        await robot_1.goto(y=Y_GRAB_IN_DOWN)
        await robot_1.set_valves([1] * 10)
        await asyncio.sleep(T_GRAB_IN)
        await robot_1.goto(y=Y_GRAB_IN_UP_2)

        print('put input into station')
        tasks = []
        # for station in stations:
        #     tasks.append(station.send_command(
        #         {'verb': 'set_valves', 'valves': [0, 0, 0, 1]}, assert_success=True))
        #
        tasks.append(robot_1.goto(x=X_PLACE_IN))
        await asyncio.gather(*tasks)

        await robot_1.goto(y=Y_PLACE_IN)
        await robot_1.set_valves([0] * 10)
        await asyncio.sleep(T_PLACE_IN_FALL)

        print('press holder in')
        await robot_1.set_valves([0] * 5 + [1] * 5)
        await asyncio.sleep(T_PLACE_IN_JACK_CLOSE)
        await robot_1.goto(y=Y_PLACE_IN_PRESS)
        await asyncio.sleep(T_PLACE_IN_PRESS)
        await robot_1.goto(y=Y_PLACE_IN_COMEOUT)
        await robot_1.set_valves([0] * 10)

        print('Move back for station to work')
        await robot_1.goto(x=X_MOVE_SAFE_STATION)

        await asyncio.gather(
            # do_station(stations, robot_1, rail, all_nodes),
            # do_rail(stations, robot_1, rail, all_nodes)
            # do_rail(robot_1)
        )

        print('deliver')
        # await run_stations(stations, lambda s: s.goto(H_DELIVER))
        await robot_1.goto(y=Y_DELIVER)
        await robot_1.goto(x=X_DELIVER)
        await robot_1.set_valves([1] * 5)
        await asyncio.sleep(T_DELIVER_PRE)
        # await run_stations(stations, lambda x: x.set_valves([0]))
        await asyncio.sleep(T_DELIVER_POST)
        # await run_stations(stations, lambda s: s.goto(H_CLEAR))

        print('Capping')

        await robot_1.goto(x=X_CAPPING)

        # await rail.set_valves([0, 1])
        await asyncio.sleep(T_RAIL_MOVING_JACK)
        # await rail.set_valves([1, 1])

        await robot_1.goto(y=Y_CAPPING_DOWN_1)

        # await rail.set_valves([0, 1])
        await asyncio.sleep(T_RAIL_FIXED_JACK)
        # await rail.set_valves([0, 0])

        await robot_1.goto(y=Y_CAPPING_DOWN_2)
        await robot_1.set_valves([0] * 10)
        await robot_1.goto(y=Y_CAPPING_UP)
        print('end of loop')

        return


async def do_rail(robot_1):
    await robot_1.goto(y=Y_MOVE_SAFE_STATION)
    await robot_1.goto(x=X_PARK)
    await robot_1.goto(y=Y_PARK)

    # await rail.goto(D_MIN)
    #
    # await rail.send_command({'verb': 'set_valves', 'valves': [0, 1]})
    # await asyncio.sleep(T_RAIL_MOVING_JACK)
    # await rail.send_command({'verb': 'set_valves', 'valves': [1, 1]})
    # await asyncio.sleep(T_RAIL_FIXED_JACK)
    #
    # await rail.goto(D_MAX)
    #
    # await rail.send_command({'verb': 'set_valves', 'valves': [0, 1]})
    # await asyncio.sleep(T_RAIL_FIXED_JACK)
    # await rail.send_command({'verb': 'set_valves', 'valves': [0, 0]})
    # await asyncio.sleep(T_RAIL_MOVING_JACK)
    #
    # await rail.goto(D_STANDBY)
