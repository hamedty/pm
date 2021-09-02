import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    print('all nodes ready')
    # stations = stations[4:]

    # # test valves
    # await test_valve(stations, valve=0, delay=1, count=40)
    # await test_valve(stations, valve=1, delay=1, count=40)
    # await test_valve(stations, valve=2, delay=1.5, count=5)
    # await test_valve(stations, valve=3, delay=1, count=10)
    # await test_valve(stations, valve=4, delay=1, count=40)

    # Motors
    # await run_many(stations, lambda x: x.set_valves([1, 1]))

    # await move_rotary_motor(stations, axis='X', amount=360, feed=10000, count=15, delay=1)
    await move_rotary_motor(stations, axis='X', amount=720, feed=30000, count=15, delay=1)
    # await move_rotary_motor(stations, axis='Y', amount=360, feed=10000, count=15, delay=1)
    # await move_rotary_motor(stations, axis='Y', amount=720, feed=30000, count=25, delay=.1)

    # Digital Inputs
    # Encoder
    # Home
    # await stations[0].home()
    # await stations[1].home()
    # await stations[2].home()
    # await stations[3].home()
    # await stations[4].home()
    # Race
    return


async def test_valve(stations, valve, delay, count):
    valves = [0] * 5
    for i in range(count):
        valves[valve] = 1 - (i % 2)
        await run_many(stations, lambda x: x.set_valves(valves))
        await asyncio.sleep(delay)


async def move_rotary_motor(stations, axis, amount, feed, count, delay):
    for i in range(count):
        amount = -amount
        await run_many(stations, lambda x: x.send_command_raw('G10 L20 P1 %s0' % axis))
        await run_many(stations, lambda x: x.send_command_raw('G1 %s%d F%d' % (axis, amount, feed)))
        await asyncio.sleep(delay)
