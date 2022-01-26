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

    for s in stations[:2]:
        # await s.set_valves([1])
        # await asyncio.sleep(.5)
        await s.G1(z=s.hw_config['H_PRE_DANCE'], feed=5000)
