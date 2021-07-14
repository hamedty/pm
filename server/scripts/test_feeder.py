import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder = await gather_feeder(system, ALL_NODES)
    print('feeder ready')

    # await feeder.set_valves([0] * 14)
    # await asyncio.sleep(.5)
    # await feeder.home()
    #
    # for i in range(10):
    #     await feeder.send_command_raw(
    #         'G1 Z180 F100000 \n'
    #         'M100 ({out9: 1}) \n'
    #         'G4 P.2 \n'
    #         'M100 ({out14: 1}) \n'
    #         'G4 P.3 \n'
    #         'M100 ({out9: 0}) \n'
    #         'G4 P.5 \n'
    #         'G1 Z5 F100000 \n'
    #         'M100 ({out14: 0}) \n'
    #         'G4 P.3 \n'
    #         'M100 ({out9: 1}) \n'
    #         'G4 P.2 \n'
    #     )

    # while True:
    #     await feeder.home()
    #     await feeder.G1(x=100, feed=6000)


async def gather_feeder(system, ALL_NODES):
    feeder = [node for node in ALL_NODES if node.name.startswith('Feeder ')][0]

    while not feeder.ready_for_command():
        await asyncio.sleep(.01)

    return feeder


async def test_valve(stations, valve, delay, count):
    valves = [0] * 5
    for i in range(count):
        valves[valve] = 1 - (i % 2)
        await run_many(stations, lambda x: x.set_valves(valves))
        await asyncio.sleep(delay)


async def move_rotary_motor(stations, axis, amount, feed, count, delay):
    for i in range(count):
        amount = -amount
        await run_many(stations, lambda x: x.send_command_raw('G10 L20 P1 %s0' % axis))
        await run_many(stations, lambda x: x.send_command_raw('G1 %s%d F%d' % (axis, amount, feed)))
        await asyncio.sleep(delay)
