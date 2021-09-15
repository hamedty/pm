import time
import asyncio
from .recipe import *
from .main import *
import traceback
import aioconsole


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)

    # stations = [stations[0]]
    # robot = robots[0]
    # robots = [robots[0]]
    # feed = 5000
    # await do_nodes(robots, lambda r: r.set_valves([0] * 10), simultanously=True)
    # await do_nodes(robots, lambda r: r.G1(y=40, feed=1000), simultanously=True)
    # for i in range(3):
    #     await do_nodes(robots, lambda r: r.G1(x=10, feed=feed), simultanously=True)
    #     await do_nodes(robots, lambda r: r.G1(x=300, feed=feed), simultanously=True)
    await rail.G1(z=5, feed=10000)
    # await rail.G1(z=250, feed=10000)
    await rail.G1(z=495, feed=10000)


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


async def do_nodes(stations, func, simultanously=True):
    if simultanously:
        res = await asyncio.gather(*[func(station) for station in stations], return_exceptions=True)
        for i in range(len(stations)):
            if isinstance(res[i], Exception):
                print('error while running for %dth station' % (i + 1))
                print(res[i])
                await aioconsole.ainput('enter to continue')
    else:
        for station in stations:
            try:
                await func(station)
            except:
                print(traceback.format_exc())
                await aioconsole.ainput('enter to continue')
