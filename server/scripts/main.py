import time
import traceback
import asyncio
import aioconsole
from .recipe import *
from scripts import recipe
from node import ALL_NODES_DICT


async def main(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    ''' Homing '''
    # a = await aioconsole.ainput('type anything to home. or enter to dismiss')
    # if a:
    #     print('homing')
    #     await home_all_nodes(system, feeder, rail, robots, stations)
    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)
    ''' Initial Condition '''
    await system.system_running.wait()

    await do_nodes(robots, lambda r: r.set_valves([0] * 10))
    await do_nodes(stations, lambda s: s.set_valves([None, 0, 0, 1, 0]))
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)

    ''' Initial Condition '''
    # feeder
    feeder.init_events()
    asyncio.create_task(feeder.feeding_loop(recipe))

    # dosing feeder
    await dosing_feeder.create_feeding_loop(feeder, recipe)

    # rail
    rail.init_events()
    asyncio.create_task(rail.rail_loop(recipe, feeder))

    # stations
    stations_loop = []
    for station in stations:
        station.init_events()
        task = asyncio.create_task(
            station.station_assembly_loop(recipe))
        stations_loop.append(task)

    ''' Fill Line '''
    # await feeder_fill_line(recipe, feeder, rail)
    feeder.feeder_initial_start_event.set()

    ''' Main Loop'''
    t0 = time.time()
    while not system.system_stop.is_set():
        # await(await system.register_error({'message': 'Ready. continue?', 'location_name': 'System'})).wait()

        # wait for rail to be parked
        await rail.rail_parked_event.wait()
        rail.rail_parked_event.clear()
        print(time.time() - t0)
        t0 = time.time()

        # do robots
        await do_nodes(robots, lambda r: r.do_robot(recipe))

        # command rail to do the next cycle
        rail.rail_move_event.set()

        # park robots
        await do_nodes(robots, lambda r: r.do_robot_park(recipe))

    ''' Clean Up '''
    rail.system_stop_event.set()
    feeder.system_stop_event.set()

    await asyncio.gather(*[station.clearance() for station in stations])
    for task in stations_loop:
        task.cancel()

    await dosing_feeder.terminate_feeding_loop(feeder)
    await feeder.set_motors()  # set all feeder motors to 0
    await feeder.set_valves([None] * 9 + [0])  # turn off air tunnel


async def home_all_nodes(feeder, rail, robots, stations):
    await system.system_running.wait()
    feeder_home = asyncio.create_task(feeder.home())

    await system.system_running.wait()
    await do_nodes(stations, lambda s: s.home())

    await system.system_running.wait()
    await do_nodes(robots, lambda r: r.home())

    await system.system_running.wait()
    await rail.home()

    await system.system_running.wait()
    await rail.G1(z=D_STANDBY, feed=FEED_RAIL_FREE * .6)
    await feeder_home


async def do_nodes(stations, func):
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
            error_clear_event, error_id = await stations[i].system.register_error(error)
            await error_clear_event.wait()


async def feeder_fill_line(recipe, feeder, rail):
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
