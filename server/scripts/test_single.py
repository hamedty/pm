import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    print('Nodes Ready')
    station = stations[3]
    await stations[3].home()
