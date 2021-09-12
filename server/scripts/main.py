import time
import traceback
import asyncio
import aioconsole
from .recipe import *
import recipe


async def main(system, ALL_NODES):
    null_awaitable = asyncio.create_task(null_func())
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    ''' Homing '''
    a = await aioconsole.ainput('type anything to home. or enter to dismiss')
    if a:
        print('homing')
        await home_all_nodes(all_nodes, feeder, rail, robots, stations)

    ''' Initial Condition '''
    await get_input(system, 'Open all robots jacks')
    await do_nodes(robots, lambda r: r.set_valves([0] * 10), simultanously=False)

    await get_input(system, 'Release all stations jack')
    await do_nodes(stations, lambda s: s.set_valves([None, None, 0, 1, 0]))

    # await get_input(system, 'start feeder motors')
    # await feeder.set_motors(
    #     (2, 4), (3, 4),  # Holder Downstream
    #     (1, 26), (4, 8), (7, 46),  # Holder Upstream - Lift and long conveyor
    #     (6, 32), (8, 200)  # Cartridge Conveyor + OralB
    # )
    # await asyncio.sleep(2)

    ''' Fill Line '''
    # await feeder_fill_line(system, feeder, rail)

    stations_task = null_awaitable
    feeder.init_events()
    asyncio.create_task(feeder.feeding_loop({'mask': [1] * N}, system))
    for station in stations:
        station.init_events()
        asyncio.create_task(station.station_assembly_loop(recipe, system))

    while True:
        '''PICK UP'''
        await get_input(system, 'Pick up')

        async def do_pickup(robot):
            Y_GRAB_IN_UP_1 = 75
            X_GRAB_IN = 284.5
            Y_GRAB_IN_DOWN = 0
            Y_GRAB_IN_UP_2 = 65
            T_GRAB_IN = 0.5
            await robot.G1(y=Y_GRAB_IN_UP_1, feed=FEED_Y_UP)
            await robot.G1(x=X_GRAB_IN, feed=FEED_X)
            await robot.G1(y=Y_GRAB_IN_DOWN, feed=FEED_Y_DOWN)
            await robot.set_valves_grab_infeed()
            await asyncio.sleep(T_GRAB_IN)
            await robot.G1(y=Y_GRAB_IN_UP_2, feed=FEED_Y_UP)

        await do_nodes(robots, lambda r: do_pickup(r), simultanously=False)

        '''EXCHANGE'''
        async def do_exchange():
            X_INPUT = 373
            Y_INPUT_DOWN_1 = 35
            Y_INPUT_UP = 55
            Y_INPUT_DOWN_3 = 6
            Y_INPUT_DOWN_2 = Y_INPUT_DOWN_3 + 10
            Y_OUTPUT = 80
            X_OUTPUT_SAFE = X_CAPPING

            FEED_Y_PRESS = 3000

            Z_OUTPUT = 70
            Z_OUTPUT_SAFE = Z_OUTPUT - 20

            T_INPUT_RELEASE = 0.5
            T_HOLDER_JACK_CLOSE = 0.5
            T_PRE_PRESS = 0.2
            T_POST_PRESS = 0.2
            T_OUTPUT_GRIPP = 0.1
            T_OUTPUT_RELEASE = 0.2

            # ensure about stations
            for station in stations:
                await station.station_is_done_event.wait()
                station.station_is_done_event.clear()
            await verify_no_holder_no_dosing(stations)

            await do_nodes(robots, lambda r: r.G1(x=X_INPUT, feed=FEED_X), simultanously=False)
            await do_nodes(robots, lambda r: r.G1(y=Y_INPUT_DOWN_1, feed=FEED_Y_DOWN), simultanously=False)
            await do_nodes(robots, lambda r: r.set_valves([0] * 10), simultanously=False)
            await asyncio.sleep(T_INPUT_RELEASE)
            await verify_dosing_sit_right(stations)

            await do_nodes(robots, lambda r: r.G1(y=Y_INPUT_UP, feed=FEED_Y_UP), simultanously=False)
            await do_nodes(robots, lambda r: r.set_valves([0] * 5 + [1] * 5), simultanously=False)
            await asyncio.sleep(T_HOLDER_JACK_CLOSE)
            await do_nodes(robots, lambda r: r.G1(y=Y_INPUT_DOWN_2, feed=FEED_Y_DOWN), simultanously=False)
            await asyncio.sleep(T_PRE_PRESS)
            await do_nodes(robots, lambda r: r.G1(y=Y_INPUT_DOWN_3, feed=FEED_Y_PRESS), simultanously=False)
            await asyncio.sleep(T_POST_PRESS)
            await do_nodes(stations, lambda s: s.G1(z=Z_OUTPUT, feed=FEED_Z_DOWN / 4.0))
            await do_nodes(robots, lambda r: r.G1(y=Y_OUTPUT, feed=FEED_Y_UP), simultanously=False)
            await do_nodes(robots, lambda r: r.set_valves([1] * 5), simultanously=False)
            await asyncio.sleep(T_OUTPUT_GRIPP)
            await do_nodes(stations, lambda s: s.set_valves([0, 0, 0, 1]))
            await asyncio.sleep(T_OUTPUT_RELEASE)
            await do_nodes(stations, lambda s: s.G1(z=Z_OUTPUT_SAFE, feed=FEED_Z_UP))
            for station in stations:
                station.station_is_full_event.set()

            await do_nodes(robots, lambda r: r.G1(x=X_OUTPUT_SAFE, feed=FEED_X), simultanously=False)
            for station in stations:
                station.station_is_safe_event.set()

        await do_exchange()

        '''CAP'''
        async def do_cap():
            await rail.set_valves([1, 0])
            await asyncio.sleep(T_RAIL_MOVING_JACK)
            await rail.set_valves([1, 1])
            await do_nodes(robots, lambda r: r.G1(x=X_CAPPING, feed=FEED_X), simultanously=False)
            await get_input(system, 'go down1?')

            await do_nodes(robots, lambda r: r.G1(y=Y_CAPPING_DOWN_1, feed=FEED_Y_DOWN), simultanously=False)
            await rail.set_valves([1, 0])
            await asyncio.sleep(T_RAIL_FIXED_JACK)
            await rail.set_valves([0, 0])
            await do_nodes(robots, lambda r: r.G1(y=Y_CAPPING_DOWN_2, feed=FEED_Y_CAPPING), simultanously=False)
            await do_nodes(robots, lambda r: r.set_valves([0] * 10), simultanously=False)
            await do_nodes(robots, lambda r: r.G1(x=X_PARK, feed=FEED_X), simultanously=False)
            await do_nodes(robots, lambda r: r.G1(y=Y_PARK, feed=FEED_Y_UP), simultanously=False)
        await do_cap()

        ''' RAIL '''
        await do_rail(rail, feeder)


async def home_all_nodes(all_nodes, feeder, rail, robots, stations):
    feeder_home = asyncio.create_task(feeder.home())
    await do_nodes(stations, lambda s: s.home())
    await do_nodes(robots, lambda r: r.home())
    await rail.home()
    await rail.G1(z=D_STANDBY, feed=FEED_RAIL_FREE * .6)
    await feeder_home


async def do_nodes(stations, func, simultanously=True):
    if simultanously:
        res = await asyncio.gather(*[func(station) for station in stations], return_exceptions=True)
        for i in range(len(stations)):
            if isinstance(res[i], Exception):
                print('error while running for %dth station' % (i + 1))
                print(res[i])
                await aioconsole.ainput('enter to continue')
    else:
        for station in stations:
            try:
                await func(station)
            except:
                print(traceback.format_exc())
                await aioconsole.ainput('enter to continue')


async def feeder_fill_line(system, feeder, rail):
    async def internal(mask):
        print(mask)
        await get_input(system, 'filling line')
        feeder_task = asyncio.create_task(feeder.send_command(
            {'verb': 'feeder_process', 'mask': mask}))

        ''' RAIL '''
        D_MIN = D_STANDBY - 25 * len(mask)
        D_MAX = D_STANDBY
        T_RAIL_JACK1 = 1.5
        T_RAIL_JACK2 = 1.5

        # rail backward
        await rail.G1(z=D_MIN, feed=FEED_RAIL_FREE)
        await feeder_task

        # change jacks to moving
        await rail.set_valves([1, 0])
        await asyncio.sleep(T_RAIL_JACK1 / 3)
        await feeder.set_valves([None, 0])
        await asyncio.sleep(T_RAIL_JACK1 * 2 / 3)
        await rail.set_valves([1, 1])
        await asyncio.sleep(T_RAIL_JACK2)

        # rail forward
        await rail.G1(z=D_MAX, feed=FEED_RAIL_INTACT)

        # change jacks to moving
        await rail.set_valves([1, 0])
        await asyncio.sleep(T_RAIL_JACK1)
        await rail.set_valves([0, 0])
        await asyncio.sleep(T_RAIL_JACK1)

        # rail park
        await rail.G1(z=D_STANDBY, feed=FEED_RAIL_FREE)

    await internal([0] * 4 + [1])
    await internal([0] * 4 + [1])
    await internal([0] * 3 + [1] * 2)
    await internal([0] * 3 + [1] * 2)
    await internal([0] * 2 + [1] * 3)
    await internal([0] * 2 + [1] * 3)
    await internal([0] * 1 + [1] * 4)
    await internal([0] * 1 + [1] * 4)
    for i in range(5):
        await internal([1] * 5)
    await internal([1] * 2)


async def verify_dosing_sit_right(stations):
    res = await asyncio.gather(*[
        station.send_command(
            {'verb': 'detect_vision', 'object': 'dosing_sit_right'})
        for station in stations])
    res = [r[1]['sit_right'] for r in res]
    if not all(res):
        print(res)
        await aioconsole.ainput('dosing not sit right (above results).')


async def verify_no_holder_no_dosing(stations):
    res_raw = await asyncio.gather(*[
        station.send_command(
            {'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
        for station in stations])
    res = [r[1]['no_holder_no_dosing'] for r in res_raw]
    if not all(res):
        print(res, res_raw)
        await aioconsole.ainput('no holder no dosing failed. above results.')


async def verify_holder_n_dosing(stations):
    results = await asyncio.gather(*[
        station.send_command(
            {'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
        for station in stations])
    for i in range(len(results)):
        station = stations[i]
        result = results[i][1]
        full = result['dosing_present'] and result['holder_present']
        empty = result['no_holder_no_dosing']
        station.full = full
        if not (full or empty):
            print(station.name, result)
            message = 'not all elements are present at %s. remove all to continue' % station.name
            await aioconsole.ainput(message)


async def do_rail(rail, feeder):
    D_MIN = D_STANDBY - 25 * N
    D_MAX = D_STANDBY
    T_RAIL_JACK1 = 1.5
    T_RAIL_JACK2 = 1.5

    # rail backward
    await rail.G1(z=D_MIN, feed=FEED_RAIL_FREE)
    await feeder.feeder_is_full_event.wait()
    feeder.feeder_is_full_event.clear()

    # change jacks to moving
    await rail.set_valves([1, 0])
    await asyncio.sleep(T_RAIL_JACK1 / 3)
    await feeder.set_valves([None, 0])
    await asyncio.sleep(T_RAIL_JACK1 * 2 / 3)
    await rail.set_valves([1, 1])
    await asyncio.sleep(T_RAIL_JACK2)

    # rail forward
    await rail.G1(z=D_MAX, feed=FEED_RAIL_INTACT)
    feeder.feeder_is_empty_event.set()

    # change jacks to moving
    await rail.set_valves([1, 0])
    await asyncio.sleep(T_RAIL_JACK1)
    await rail.set_valves([0, 0])
    await asyncio.sleep(T_RAIL_JACK1)

    # rail park
    await rail.G1(z=D_STANDBY, feed=FEED_RAIL_FREE)
