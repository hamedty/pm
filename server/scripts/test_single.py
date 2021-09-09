import time
import asyncio
from .recipe import *
import traceback
import aioconsole


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    print('Nodes Ready')

    while True:
        await feeder.set_motors((2, 10), (3, 4))
        await asyncio.sleep(.5)
        await feeder.set_motors((2, 4), (3, 4))
        await asyncio.sleep(.5)


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
