import time
import asyncio
from .main import *
import traceback
import aioconsole
from .recipe import *
from scripts import recipe


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    stations = stations[4:]
    # H_ALIGNING H_PUSH H_PRE_DANCE
    # for station in stations:
    #     await station.G1(z=station.hw_config['H_PUSH'], feed=500)
    #     await asyncio.sleep(1)

    v = 0
    while True:
        v = 1 - v
        await asyncio.gather(*[station.set_valves([0, 0, v]) for station in stations])
        await asyncio.sleep(2)
