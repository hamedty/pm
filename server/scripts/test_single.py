import time
from .main import *
import asyncio
import traceback
import aioconsole
from .recipe import *
from scripts import recipe
from node import ALL_NODES_DICT


async def main(system, ALL_NODES):
    all_nodes, feeder, dosing_feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)
    r = robots[1]

    # await r.G1(y=30, feed=2000)
    # await r.send_command_raw('{xjm:10000}')
    # f = 30000
    # t0 = time.time()
    # await r.G1(x=370, feed=f)
    # await asyncio.sleep(.5)
    # await r.G1(x=10, feed=f)
    # t1 = time.time()
    # print(t1 - t0 - .5)

    # await r.send_command_raw('{xjm:10000}')
    # f = 35000
    # t0 = time.time()
    # await r.G1(x=370, feed=f)
    # await asyncio.sleep(.5)
    # await r.G1(x=280, feed=f - 2000)
    # t1 = time.time()
    # print(t1 - t0 - .5)

    await r.G1(x=10, feed=5000)

    await r.send_command_raw('{yjm:15000}')
    f_up = 35000
    f_down = 40000

    t0 = time.time()
    await r.G1(y=70, feed=f_up)
    await asyncio.sleep(.5)
    await r.G1(y=5, feed=f_down)
    t1 = time.time()
    print(t1 - t0 - .5)
