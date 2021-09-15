import time
import traceback
import asyncio
import aioconsole
from .recipe import *
from scripts import recipe


async def main(system, ALL_NODES):
    null_awaitable = asyncio.create_task(null_func())
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    ''' Homing '''
    a = await aioconsole.ainput('type anything to home. or enter to dismiss')
    if a:
        print('homing')
        await home_all_nodes(all_nodes, feeder, rail, robots, stations)

    ''' Initial Condition '''
    # await get_input(system, 'Open all robots jacks')
    await do_nodes(robots, lambda r: r.set_valves([0] * 10), simultanously=False)

    # await get_input(system, 'Release all stations jack')
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
        await do_nodes(robots, lambda r: r.do_robot(recipe, system), simultanously=True)
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
