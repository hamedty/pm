import time
import traceback
import asyncio

from .recipe import *
from .utils import *
from scripts import recipe
from node import ALL_NODES_DICT


@run_exclusively
async def main(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    ''' Initial Condition '''
    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)
    await system.system_running.wait()

    await do_nodes(robots, lambda r: r.set_valves([0] * 10))
    await do_nodes(stations, lambda s: s.set_valves([None, 0, 0, 1, 0]))
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)

    ''' Initial Condition '''
    # feeder
    feeder.init_events()
    feeder_loop_task = asyncio.create_task(feeder.feeding_loop(recipe))

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
    feeder.feeder_initial_start_event.set()

    ''' Main Loop'''
    t0 = time.time()
    t1 = time.time()
    i = 0
    while not system.system_stop.is_set():
        # error_clear_event, error_id = await system.register_error({'message': 'دور بعدی شروع شود?', 'location_name': 'System', 'type': 'error'})
        # await error_clear_event.wait()

        # wait for rail to be parked
        await rail.rail_parked_event.wait()
        rail.rail_parked_event.clear()
        print(f'rail portion: {time.time() - t1:.1f}')
        print(f'\t\t\t\t\t\t\tcomplete: {time.time() - t0:.1f}')
        t0 = time.time()

        # do robots
        await do_nodes(robots, lambda r: r.do_robot(recipe))
        t1 = time.time()
        dt = t1 - t0
        print(f'robot portion: {dt:.1f}')
        system.mongo.write('timing', {'robots': dt})

        # command rail to do the next cycle
        rail.rail_move_event.set()

        # park robots
        await do_nodes(robots, lambda r: r.do_robot_park(recipe))
        i += 1
        print('--------------------------------', i)

    ''' Clean Up '''
    rail.system_stop_event.set()
    feeder.system_stop_event.set()

    await asyncio.gather(*[station.clearance() for station in stations])
    for task in stations_loop:
        task.cancel()

    await feeder_loop_task
    await dosing_feeder.terminate_feeding_loop(feeder)
    await feeder.set_motors()  # set all feeder motors to 0
    await feeder.set_valves([None] * 9 + [0])  # turn off air tunnel


@run_exclusively
async def home_all_nodes(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

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
    # , return_exceptions=True)
    res = await asyncio.gather(*[func(station) for station in stations])
    for i in range(len(stations)):
        if isinstance(res[i], Exception):
            error = {
                'message': 'خطاپیچیده در: %s' % stations[i].name,
                'location_name': stations[i].name,
                'details': res[i],
                'type': 'error',
            }
            print(error)
            # await aioconsole.ainput(str(error))
            error_clear_event, error_id = await stations[i].system.register_error(error)
            await error_clear_event.wait()
