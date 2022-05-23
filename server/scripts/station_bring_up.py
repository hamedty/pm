import time
from .main import *
import asyncio
import traceback
from .utils import *
from node import ALL_NODES_DICT


@run_exclusively
async def home_station(system, ALL_NODES):

    s = ALL_NODES_DICT['Station X']

    while not s.ready_for_command():
        await asyncio.sleep(.01)

    await s.home()

    s.init_events()
    s.main_loop_task = asyncio.create_task(s.station_assembly_loop())


async def station_is_full(system, ALL_NODES):
    system.system_running.set()

    s = ALL_NODES_DICT['Station X']
    s.station_is_full_event.set()
    s.station_is_safe_event.set()
