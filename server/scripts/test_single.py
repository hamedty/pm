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

    # stations = stations[4:]
    # H_ALIGNING H_PUSH H_PRE_DANCE
    # for station in stations:
    #     await station.G1(z=station.hw_config['H_ALIGNING'], feed=5000)
    #     await asyncio.sleep(1)

    # v = 0
    # while True:
    #     v = 1 - v
    #     await asyncio.gather(*[station.set_valves([0, 0, v]) for station in stations])
    #     await asyncio.sleep(2)

    # # await feeder.home()
    # t0 = time.time()
    # z = 16
    # feed = 50000
    # # for i in range(10):
    # #     z += 25
    # #     await feeder.G1(z=z, feed=feed)
    # command = ''
    # for i in range(10):
    #     z += 25
    #     command += 'G1Z%dF%d\n' % (z, feed)
    #
    # await feeder.send_command_raw(command)
    #
    # node = ALL_NODES_DICT['Dosing Feeder 1']
    # for i in range(50):
    #     await node.set_valves([i % 2])
    #     await asyncio.sleep(0.8)

    dosing_feeder = ALL_NODES_DICT['Dosing Feeder 1']
    holder_feeder = ALL_NODES_DICT['Feeder 1']

    # start dosing conveyor motor
    await holder_feeder.set_motors((5, 25), (9, 5))
    # await holder_feeder.set_valves([None] * 10 + [1])
    try:
        # for i in range(100):
        while True:

            # set channel selector 1= channel 1 open
            # await dosing_feeder.set_valves([0, None, 1])

            # wait for optic sensor input=1
            await dosing_feeder.wait_metric('in1')

            # wait for buffer to be free
            await dosing_feeder.wait_metric('in3', 0)

            # close gate
            await dosing_feeder.set_valves([None, None, 0])

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
