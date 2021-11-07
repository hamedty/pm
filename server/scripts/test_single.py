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

    # await feeder.set_motors((4, 8), (7, 46))
    # while True:
    #     await feeder.set_valves([None, None, 1])
    #     await asyncio.sleep(0.25)
    #     await feeder.set_valves([None, None, 0])
    #     await asyncio.sleep(3)

    # for i in range(20):
    #     await stations[8].set_valves([0] * 4 + [i % 2])
    #     await stations[9].set_valves([0] * 4 + [i % 2])
    #     await asyncio.sleep(1)
    t = 0.2
    for i in range(10):
        await asyncio.sleep(t)
        tt = asyncio.create_task(dance(stations[i], t))
    await tt


async def dance(station, t):
    while True:
        await station.set_valves([0] * 5 + [1])
        await asyncio.sleep(t + .1)
        await station.set_valves([0] * 5 + [0])
        await asyncio.sleep(t * 9 - .1)
