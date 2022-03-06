import time
import asyncio
from .main import *
from .utils import *
import aioconsole


@run_exclusively
async def feed16(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)

    ''' Inits '''
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)
    feeder.init_events()

    dosing_loop_task = asyncio.create_task(
        dosing_feeder.dosing_master_loop(feeder))

    ''' main task '''
    # 1st round
    mask_holder = [0] * 10
    mask_dosing = [0] * 4 + [1] * 6
    await feeder.feeder_process(mask_holder, mask_dosing)
    await feeder_handover_to_rail_bare(system, ALL_NODES)
    # 2nd round
    mask_holder = [0] * 10
    mask_dosing = [1] * 10
    await feeder.feeder_process(mask_holder, mask_dosing)
    await feeder_handover_to_rail_bare(system, ALL_NODES)

    ''' clean up '''
    feeder.system_stop_event.set()
    await dosing_loop_task
    await dosing_feeder.terminate_feeding_loop(feeder)
    await feeder.set_motors()  # set all feeder motors to 0
    await feeder.set_valves([None] * 9 + [0])  # turn off air tunnel


@run_exclusively
async def fill_cartridge_conveyor(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    await feeder.set_motors(
        (6, 300),  # Cartridge Conveyor
        (8, 20),  # Cartridge Conveyor
    )


@run_exclusively
async def fill_dosing_rail(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    await dosing_feeder.create_feeding_loop(feeder)
    await asyncio.sleep(20)
    await dosing_feeder.terminate_feeding_loop(feeder)


@run_exclusively
async def run_rail_empty(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)

    ''' Initial Condition '''
    # feeder
    feeder.init_events()

    # rail
    rail.init_events()
    asyncio.create_task(rail.rail_loop(feeder))

    ''' Main Loop'''
    for i in range(2):
        if system.system_stop.is_set():
            break
        await rail.rail_parked_event.wait()
        rail.rail_parked_event.clear()
        rail.rail_move_event.set()
        feeder.feeder_is_full_event.set()

    await rail.rail_parked_event.wait()
    rail.system_stop_event.set()


@run_exclusively
async def feeder_handover_to_rail(*args, **kwargs):
    await feeder_handover_to_rail_bare(*args, **kwargs)


async def feeder_handover_to_rail_bare(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    # rail, feeder homed and parked
    assert await rail.is_homed(), 'Rail is not homed!'
    assert await feeder.is_homed(), 'Feeder is not homed!'
    assert rail.is_at_loc(z=rail.recipe.D_STANDBY) or rail.is_at_loc(
        z=rail.recipe.D_MIN), 'rail is in bad location'
    # assert feeder.is_at_loc(z=feeder.recipe.FEEDER_Z_DELIVER) or feeder.is_at_loc(
    #     z=feeder.recipe.FEEDER_Z_IDLE), 'feeder is in bad location'

    # jack's to normal
    await rail.set_valves([0, 0])

    await feeder.G1(z=feeder.recipe.FEEDER_Z_DELIVER, feed=feeder.recipe.FEED_FEEDER_DELIVER), 'feeder is in bad location'
    await rail.G1(z=rail.recipe.D_MIN, feed=rail.recipe.FEED_RAIL_FREE)
    await rail.set_valves([1, 0])
    await asyncio.sleep(rail.recipe.T_RAIL_FEEDER_JACK)
    await feeder.set_valves([None, 0])
    await asyncio.sleep(rail.recipe.T_RAIL_JACK1 - rail.recipe.T_RAIL_FEEDER_JACK)
    await rail.set_valves([1, 1])
    await asyncio.sleep(rail.recipe.T_RAIL_JACK2)
    await rail.send_command_raw(f'''
        G1 Z50 F{rail.recipe.FEED_RAIL_INTACT / 4}
        G1 Z{rail.recipe.D_STANDBY} F{rail.recipe.FEED_RAIL_INTACT}
    ''')
    await rail.G1(z=rail.recipe.D_STANDBY, feed=rail.recipe.FEED_RAIL_INTACT)
    await rail.set_valves([1, 0])
    await asyncio.sleep(rail.recipe.T_RAIL_JACK1)
    await rail.set_valves([0, 0])
    await asyncio.sleep(rail.recipe.T_RAIL_JACK2)


@run_exclusively
async def motors_off(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    await feeder.set_motors()
    valves = [0] * 14
    valves[1] = None  # comb
    await feeder.set_valves(valves)


@run_exclusively
async def motors_on(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    await feeder.set_motors(
        (2, 4), (3, 4),  # Holder Downstream
        # Holder Upstream - Lift and long conveyor
        (4, 4), (7, 11),
        (1, 3750), (10, 35000),  # holder gate on/off
        (6, 25),  (8, 8)  # Cartridge Conveyor + Randomizer
    )
    await dosing_feeder.set_motors_highlevel(feeder, 'on')
