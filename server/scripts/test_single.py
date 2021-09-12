import time
import asyncio
from .recipe import *
from .main import *
import traceback
import aioconsole


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    # for i in range(5):
    #     await rail.set_valves([1, 0])
    #     await asyncio.sleep(.6)
    #     await rail.set_valves([1, 1])
    #     await asyncio.sleep(.6)
    #     await rail.G1(z=400, feed=16000)
    #
    #     await rail.set_valves([1, 0])
    #     await asyncio.sleep(.6)
    #     await rail.set_valves([0, 0])
    #     await asyncio.sleep(.6)
    #     await rail.G1(z=100, feed=30000)

    # async def do_pickup(robot):
    #     Y_GRAB_IN_UP_1 = 75
    #     X_GRAB_IN = 284.5
    #     Y_GRAB_IN_DOWN = 0
    #     Y_GRAB_IN_UP_2 = 65
    #     T_GRAB_IN = 0.5
    #     await robot.G1(y=Y_GRAB_IN_UP_1, feed=FEED_Y_UP)
    #     await robot.G1(x=X_GRAB_IN, feed=FEED_X)
    #     await robot.G1(y=Y_GRAB_IN_DOWN, feed=FEED_Y_DOWN)
    #     await robot.set_valves_grab_infeed()
    #     await asyncio.sleep(T_GRAB_IN)
    #     await robot.G1(y=Y_GRAB_IN_UP_2, feed=FEED_Y_UP)
    #
    # await do_nodes(robots, lambda r: do_pickup(r), simultanously=False)
    await verify_no_holder_no_dosing(stations)
    for station in stations:
        print(station.holder_roi)
        print(station.hw_config['holder_webcam_direction'])


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
