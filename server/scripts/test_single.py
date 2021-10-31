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

    error = {
        'message': 'Not all elements are present in the station. Remove all to continue.',
        'location_name': 'Station 12',
        'details': 'random string',
    }
    print(error)

    error_clear_event = await system.register_error(error)
    await error_clear_event.wait()
