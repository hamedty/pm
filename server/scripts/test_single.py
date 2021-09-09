import time
import asyncio
from .recipe import *
import traceback
import aioconsole


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    print('Nodes Ready')

    # async def do_pickup(robot):
    #     Y_GRAB_IN_UP_1 = 75
    #     X_GRAB_IN = 284.5
    #     Y_GRAB_IN_DOWN = 0
    #     Y_GRAB_IN_UP_2 = 65
    #     T_GRAB_IN = 0.5
    #     await robot.G1(y=Y_GRAB_IN_UP_1, feed=FEED_Y_UP)
    #     await robot.G1(x=X_GRAB_IN, feed=FEED_X)
    #     await robot.G1(y=Y_GRAB_IN_DOWN, feed=FEED_Y_DOWN)
    #     await robot.set_valves([1] * 10)
    #     # await asyncio.sleep(T_GRAB_IN)
    #     # await robot.G1(y=Y_GRAB_IN_UP_2, feed=FEED_Y_UP)
    #
    # await do_pickup(robots[1])
    await robots[1].set_valves([0] * 10)


async def test_valve(stations, delay, count):
    for i in range(count):
        valves = [1 - (i % 2)] * 10
        await run_many(stations, lambda x: x.set_valves(valves))
        await asyncio.sleep(delay)


async def move_rotary_motor(stations, axis, amount, feed, count, delay):
    for i in range(count):
        amount = -amount
        await run_many(stations, lambda x: x.send_command_raw('G10 L20 P1 %s0' % axis))
        await run_many(stations, lambda x: x.send_command_raw('G1 %s%d F%d' % (axis, amount, feed)))
        await asyncio.sleep(delay)
