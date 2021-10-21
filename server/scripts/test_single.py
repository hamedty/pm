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

    await dosing_feeder.create_feeding_loop(feeder, system, recipe)

    try:
        await asyncio.sleep(100000)
    except:
        pass

    await dosing_feeder.terminate_feeding_loop()
