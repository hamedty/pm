import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    print('all nodes ready')
    # await verify_dosing_sit_right(stations)
    await stations[8].home()


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


async def verify_dosing_sit_right(stations):
    res = await asyncio.gather(*[
        station.send_command(
            {'verb': 'detect_vision', 'object': 'dosing_sit_right'})
        for station in stations])
    print(res)
    res = [r[1]['sit_right'] for r in res]
    print(res)
    if not all(res):
        raise Exception('Station failed on verify_dosing_sit_right', res)
