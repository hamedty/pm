import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    print('all nodes ready')
    await verify_no_holder_no_dosing(stations)
    # await robots[1].restart_arduino()


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


async def verify_no_holder_no_dosing(stations):
    res = await asyncio.gather(*[
        station.send_command(
            {'verb': 'detect_vision', 'object': 'no_holder_no_dosing'})
        for station in stations])
    res = [r[1]['no_holder_no_dosing'] for r in res]
    if not all(res):
        raise Exception('Station failed on verify_no_holder_no_dosing', res)
