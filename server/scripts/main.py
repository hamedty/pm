import time
import traceback
import asyncio
import aioconsole
from .recipe import *
from scripts import recipe


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    ''' Homing '''
    a = await aioconsole.ainput('type anything to home. or enter to dismiss')
    if a:
        print('homing')
        await home_all_nodes(system, feeder, rail, robots, stations)

    ''' Initial Condition '''
    await system.system_running.wait()

    await do_nodes(system, robots, lambda r: r.set_valves([0] * 10), simultanously=False)
    await do_nodes(system, stations, lambda s: s.set_valves([None, None, 0, 1, 0]))
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)
    await feeder.set_motors(
        (2, 4), (3, 4),  # Holder Downstream
        (1, 26), (4, 8), (7, 46),  # Holder Upstream - Lift and long conveyor
        (6, 32), (8, 200)  # Cartridge Conveyor + OralB
    )
    await asyncio.sleep(2)

    ''' Initial Condition '''
    # feeder
    feeder.init_events()
    asyncio.create_task(feeder.feeding_loop(system, recipe))

    # rail
    rail.init_events()
    asyncio.create_task(rail.rail_loop(system, recipe, feeder))

    # stations
    stations_loop = []
    for station in stations:
        station.init_events()
        task = asyncio.create_task(
            station.station_assembly_loop(recipe, system))
        stations_loop.append(task)

    ''' Fill Line '''
    # await feeder_fill_line(system, recipe, feeder, rail)
    feeder.feeder_initial_start_event.set()

    ''' Main Loop'''
    while not system.system_stop.is_set():
        # wait for rail to be parked
        await rail.rail_parked_event.wait()
        rail.rail_parked_event.clear()

        # do robots
        await do_nodes(system, robots, lambda r: r.do_robot(recipe, system), simultanously=True)

        # command rail to do the next cycle
        if not system.system_stop.is_set():
            rail.rail_move_event.set()

        # park robots
        await do_nodes(system, robots, lambda r: r.do_robot_park(recipe, system), simultanously=True)

    ''' Clean Up '''
    await asyncio.gather(*[station.clearance(system) for station in stations])
    for task in stations_loop:
        task.cancel()

    for i in range(1, 10):
        await feeder.set_motors((i, 0))


async def home_all_nodes(system, feeder, rail, robots, stations):
    await system.system_running.wait()
    feeder_home = asyncio.create_task(feeder.home())

    await system.system_running.wait()
    await do_nodes(system, stations, lambda s: s.home())

    await system.system_running.wait()
    await do_nodes(system, robots, lambda r: r.home())

    await system.system_running.wait()
    await rail.home()

    await system.system_running.wait()
    await rail.G1(z=D_STANDBY, feed=FEED_RAIL_FREE * .6)
    await feeder_home


async def do_nodes(system, stations, func, simultanously=True):
    if simultanously:
        res = await asyncio.gather(*[func(station) for station in stations], return_exceptions=True)
        for i in range(len(stations)):
            if isinstance(res[i], Exception):
                error = {
                    'message': 'error while running for %dth' % (i + 1),
                    'location_name': stations[i].name,
                    'details': res[i],
                }
                print(error)
                # await aioconsole.ainput(str(error))
                error_clear_event = await system.register_error(error)
                await error_clear_event.wait()
    else:
        for station in stations:
            try:
                await func(station)
            except:
                error = {
                    'message': 'error - exception raised',
                    'location_name': station.name,
                    'details': traceback.format_exc(),
                }
                print(error)
                # await aioconsole.ainput(str(error))
                error_clear_event = await system.register_error(error)
                await error_clear_event.wait()


async def feeder_fill_line(system, recipe, feeder, rail):
    masks = [
        [0] * 4 + [1],
        [0] * 4 + [1],
        [0] * 3 + [1] * 2,
        [0] * 3 + [1] * 2,
        [0] * 2 + [1] * 3,
        [0] * 2 + [1] * 3,
        [0] * 1 + [1] * 4,
        [0] * 1 + [1] * 4,
        [1] * 5,
        [1] * 5,
        [1] * 5,
        [1] * 5,
        [1] * 5,
        [1] * 2,
    ]
    i = 0
    for mask in masks:
        if (i % 3) == 0:
            await aioconsole.ainput('enter to continue')
        i += 1
        # setup feeder
        feeder.mask = mask
        feeder.feeder_initial_start_event.set()

        await rail.rail_parked_event.wait()
        rail.rail_parked_event.clear()
        rail.N = len(mask)
        rail.rail_move_event.set()

        await feeder.feeder_finished_command_event.wait()
        feeder.feeder_finished_command_event.clear()

    feeder.mask = None  # default
