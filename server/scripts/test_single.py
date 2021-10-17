import time
from .main import *
import asyncio
import traceback
import aioconsole
from .recipe import *
from scripts import recipe
from node import ALL_NODES_DICT


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES, wait_for_readiness=False)

    dosing_feeder = ALL_NODES_DICT['Dosing Feeder 1']
    holder_feeder = ALL_NODES_DICT['Feeder 1']

    # start dosing conveyor motor
    await holder_feeder.set_motors((5, 25), (9, 5))
    # await holder_feeder.set_valves([None] * 10 + [1])
    try:
        while True:
            # wait for optic sensor input=1
            await dosing_feeder.wait_metric('in1')

            # wait for buffer to be free
            await dosing_feeder.wait_metric('in3', 0)

            # wait for proximity_input value established
            await asyncio.sleep(.2)
            proximity_input = await dosing_feeder.read_metric('in2')
            await dosing_feeder.set_valves([None, proximity_input])

            # wait for jacks to be stable
            await asyncio.sleep(.2)
            await dosing_feeder.set_valves([1])
            await asyncio.sleep(.5)
            await dosing_feeder.set_valves([0])
            await asyncio.sleep(.05)
    except:
        trace = traceback.format_exc()
        print(trace)

    await dosing_feeder.set_valves([0, None, 0])
    await holder_feeder.set_motors((5, 0), (9, 0))
