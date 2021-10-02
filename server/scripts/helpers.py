import time
import asyncio
from .main import *
from .recipe import *
from scripts import recipe
import aioconsole


async def fill_cartridge_conveyor(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    await feeder.set_motors(
        (6, 300),  # Cartridge Conveyor
    )


async def run_rail_empty(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)
    await rail.set_valves([0, 0])
    await feeder.set_valves([0] * 14)

    while system.system_running.is_set():
        await rail.set_valves([0] * 2)
        await system.system_running.wait()
        await rail.G1(z=25, feed=recipe.FEED_RAIL_FREE, system=system)
        await rail.set_valves([1, 0])
        await asyncio.sleep(recipe.T_RAIL_JACK1)
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
    await check_home_all_nodes(system, all_nodes, feeder, rail, robots, stations)

    robot = robots[0]
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
    Y_INPUT_DOWN_RELEASE_HOLDER = 36
    Y_INPUT_DOWN_RELEASE_DOSING = 32
    Y_INPUT_UP = 55
    Y_INPUT_DOWN_PRESS_HOLDER = 6
    Y_INPUT_DOWN_PRE_PRESS_HOLDER = Y_INPUT_DOWN_PRESS_HOLDER + 10
    Y_OUTPUT = 80
    X_OUTPUT_SAFE = recipe.X_CAPPING

    Z_OUTPUT = 70
    Z_OUTPUT_SAFE = Z_OUTPUT - 20

    T_INPUT_RELEASE = 1.1
    T_HOLDER_JACK_CLOSE = 0.1
    T_PRE_PRESS = 0.05
    T_POST_PRESS = 0.1
    T_OUTPUT_GRIPP = 0.1
    T_OUTPUT_RELEASE = 0.2

    await robot.G1(x=X_INPUT - .5, feed=recipe.FEED_X, system=system)

    await robot.G1(y=50, feed=recipe.FEED_Y_DOWN, system=system)
    await aioconsole.ainput('continue?')

    await robot.G1(y=Y_INPUT_DOWN_RELEASE_HOLDER, feed=recipe.FEED_Y_DOWN, system=system)
    await robot.set_valves([None] * 5 + [0] * 5)
    await robot.G1(y=Y_INPUT_DOWN_RELEASE_DOSING, feed=recipe.FEED_Y_DOWN, system=system)
    await robot.set_valves([0] * 10)
    await asyncio.sleep(T_INPUT_RELEASE)
    await robot.G1(y=Y_INPUT_UP, feed=recipe.FEED_Y_UP, system=system)
    await robot.set_valves([0] * 5 + [1] * 5)
    await asyncio.sleep(T_HOLDER_JACK_CLOSE)
    await robot.G1(y=Y_INPUT_DOWN_PRE_PRESS_HOLDER, feed=recipe.FEED_Y_DOWN, system=system)
    await asyncio.sleep(T_PRE_PRESS)
    await robot.G1(y=Y_INPUT_DOWN_PRESS_HOLDER, feed=recipe.FEED_Y_PRESS, system=system)
    await asyncio.sleep(T_POST_PRESS)
    await robot.set_valves([0] * 10)
    await robot.G1(y=Y_OUTPUT, feed=recipe.FEED_Y_UP, system=system)
