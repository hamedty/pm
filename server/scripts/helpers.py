import time
import asyncio
from .main import *
from .recipe import *
from scripts import recipe


async def fill_cartridge_conveyor(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    await feeder.set_motors(
        (6, 300),  # Cartridge Conveyor
    )


async def run_rail_empty(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    check_home_all_nodes(system, feeder, rail, robots, stations)
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)

    while system.system_running.is_set():
        await rail.set_valves([0] * 2)
        await system.system_running.wait()
        await rail.G1(z=25, feed=recipe.FEED_RAIL_FREE, system=system)
        await rail.set_valves([1, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK1 * recipe.T_RAIL_FEEDER_JACK_PERCENTAGE)
        await asyncio.sleep(recipe.T_RAIL_JACK1 * (1 - recipe.T_RAIL_FEEDER_JACK_PERCENTAGE))
        await rail.set_valves([1, 1])
        await asyncio.sleep(recipe.T_RAIL_JACK2)

        # rail forward
        await rail.G1(z=recipe.D_STANDBY, feed=recipe.FEED_RAIL_INTACT, system=system)

        # change jacks to moving
        await rail.set_valves([1, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK1)
        await rail.set_valves([0, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK2)


async def pickup_rail(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    check_home_all_nodes(system, feeder, rail, robots, stations)

    robot = robots[1]
    Y_GRAB_IN_UP_1 = 75
    X_GRAB_IN = 284.5
    Y_GRAB_IN_DOWN = 0
    Y_GRAB_IN_UP_2 = 65
    T_GRAB_IN = 0.5

    await robot.G1(y=Y_GRAB_IN_UP_1, feed=recipe.FEED_Y_UP)
    await robot.G1(x=X_GRAB_IN, feed=recipe.FEED_X)
    await robot.G1(y=Y_GRAB_IN_DOWN, feed=recipe.FEED_Y_DOWN)
    await robot.set_valves_grab_infeed()
    await asyncio.sleep(T_GRAB_IN)
    await robot.G1(y=Y_GRAB_IN_UP_2, feed=recipe.FEED_Y_UP)

    X_INPUT = 373
    Y_INPUT_DOWN_1 = 50

    await robot.G1(x=X_INPUT, feed=recipe.FEED_X)
    await robot.G1(y=Y_INPUT_DOWN_1, feed=recipe.FEED_Y_DOWN)
