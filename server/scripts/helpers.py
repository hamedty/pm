import time
import asyncio
from .main import *
from recipe import *
from .utils import *
import recipe
import aioconsole


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
    await dosing_feeder.create_feeding_loop(feeder, recipe)
    await asyncio.sleep(20)
    await dosing_feeder.terminate_feeding_loop(feeder)


@run_exclusively
async def run_rail_empty(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)

    await system.system_running.wait()

    while system.system_running.is_set():
        await rail.set_valves([0] * 2)
        await system.system_running.wait()
        await rail.G1(z=recipe.D_MIN, feed=recipe.FEED_RAIL_FREE)
        await rail.set_valves([1, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK1)
        await rail.set_valves([1, 1])
        await asyncio.sleep(recipe.T_RAIL_JACK2)

        # rail forward
        await rail.G1(z=recipe.D_STANDBY, feed=recipe.FEED_RAIL_INTACT)

        # change jacks to moving
        await rail.set_valves([1, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK1)
        await rail.set_valves([0, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK2)


@run_exclusively
async def feeder_handover_to_rail(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    # rail, feeder homed and parked
    assert await rail.is_homed(), 'Rail is not homed!'
    assert await feeder.is_homed(), 'Feeder is not homed!'
    assert rail.is_at_loc(z=D_STANDBY) or rail.is_at_loc(
        z=D_MIN), 'rail is in bad location'
    # assert feeder.is_at_loc(z=FEEDER_Z_DELIVER) or feeder.is_at_loc(
    #     z=FEEDER_Z_IDLE), 'feeder is in bad location'

    # jack's to normal
    await rail.set_valves([0, 0])

    await feeder.G1(z=FEEDER_Z_DELIVER, feed=5000), 'feeder is in bad location'
    await rail.G1(z=recipe.D_MIN, feed=recipe.FEED_RAIL_FREE)
    await rail.set_valves([1, 0])
    await asyncio.sleep(recipe.T_RAIL_FEEDER_JACK)
    await feeder.set_valves([None, 0])
    await asyncio.sleep(recipe.T_RAIL_JACK1 - recipe.T_RAIL_FEEDER_JACK)
    await rail.set_valves([1, 1])
    await asyncio.sleep(recipe.T_RAIL_JACK2)
    await rail.G1(z=recipe.D_STANDBY, feed=recipe.FEED_RAIL_INTACT)
    await rail.set_valves([1, 0])
    await asyncio.sleep(recipe.T_RAIL_JACK1)
    await rail.set_valves([0, 0])
    await asyncio.sleep(recipe.T_RAIL_JACK2)


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
