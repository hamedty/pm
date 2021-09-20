import time
import asyncio
from .main import *
import traceback
import aioconsole
from .recipe import *
from scripts import recipe


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

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
    Y_INPUT_DOWN_1 = 35
    Y_INPUT_UP = 55
    Y_INPUT_DOWN_3 = 6
    Y_INPUT_DOWN_2 = Y_INPUT_DOWN_3 + 10
    Y_OUTPUT = 80
    X_OUTPUT_SAFE = recipe.X_CAPPING

    FEED_Y_PRESS = 3000

    Z_OUTPUT = 70
    Z_OUTPUT_SAFE = Z_OUTPUT - 20

    T_INPUT_RELEASE = 1.0
    T_HOLDER_JACK_CLOSE = 0.1
    T_PRE_PRESS = 0.05
    T_POST_PRESS = 0.1
    T_OUTPUT_GRIPP = 0.1
    T_OUTPUT_RELEASE = 0.2
    await robot.G1(x=X_INPUT, feed=recipe.FEED_X)

    #
    # while True:
    #     await rail.set_valves([0] * 2)
    #     await system.system_running.wait()
    #     await rail.G1(z=recipe.D_MIN, feed=recipe.FEED_RAIL_FREE)
    #     await rail.set_valves([1, 0])
    #     await asyncio.sleep(recipe.T_RAIL_JACK1 * recipe.T_RAIL_FEEDER_JACK_PERCENTAGE)
    #     await asyncio.sleep(recipe.T_RAIL_JACK1 * (1 - recipe.T_RAIL_FEEDER_JACK_PERCENTAGE))
    #     await rail.set_valves([1, 1])
    #     await asyncio.sleep(recipe.T_RAIL_JACK2)
    #
    #     # rail forward
    #     await rail.G1(z=recipe.D_STANDBY, feed=recipe.FEED_RAIL_INTACT)
    #
    #     # change jacks to moving
    #     await rail.set_valves([1, 0])
    #     await asyncio.sleep(recipe.T_RAIL_JACK1)
    #     await rail.set_valves([0, 0])
    #     await asyncio.sleep(recipe.T_RAIL_JACK2)
