import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    feeder = await gather_feeder(system, ALL_NODES)
    print('feeder ready')

    await feeder.set_valves([0] * 14)
    # await asyncio.sleep(.5)
    await feeder.home()

    # await feeder.set_valves([None, 1])
    #
    # t0 = time.time()
    # for i in range(11):
    #     print('hi')
    #     # await feeder.send_command_raw(
    #     #     # bring finger down (7) and open sub-gate(4)
    #     #     'M100 ({out7: 1, out4: 0}) \n'
    #     #     'G4 P.2 \n'
    #     # )
    #     # await feeder.send_command_raw(
    #     #     # open main gate
    #     #     'M100 ({out3: 1}) \n'
    #     #     'G4 P.2 \n'
    #     # )
    #     # await feeder.send_command_raw(
    #     #     # push forward
    #     #     'M100 ({out6: 1}) \n'
    #     #     # 'G4 P.6 \n'
    #     # )
    #     # await asyncio.sleep(.5)
    #     # await feeder.send_command_raw(
    #     #     # close main gate again and close sub-gate
    #     #     'M100 ({out3: 0, out4: 1}) \n'
    #     #     # 'G4 P.2 \n'
    #     # )
    #     # await feeder.send_command_raw(
    #     #     # bring up finger
    #     #     'M100 ({out7: 0}) \n'
    #     #     # 'G4 P.2 \n'
    #     # )
    #
    #     x = 16 + 25 * (i + 1)
    #     c = (
    #         # bring pusher back
    #         # 'M100 ({out6: 0}) \n'
    #         # 'G4 P1.5 \n'
    #         'G1 X%d F6000\n' % x
    #     )
    #
    #     print(c)
    #     await feeder.send_command_raw(c)
    #     # await feeder.send_command_raw('G1 X%d F6000' % x)
    #     print('-------------------', i)
    #     # await asyncio.sleep(1)
    # print(time.time() - t0)
    # # await feeder.send_command_raw('G1 X719 F6000')
    # await feeder.G1(x=719, feed=6000)
    # await feeder.send_command_raw('M100 ({out2: 0}) \n')
    # await feeder.G1(x=16, feed=6000)
    # # await feeder.send_command_raw('G1 X16 F6000')
    # print(time.time() - t0)
    # print('bye')
    # # cartridge
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

    # holder
    # await asyncio.sleep(3)
    # for i in range(1):
    #     await feeder.send_command_raw(
    #         # bring finger down (7) and open sub-gate(4)
    #         'M100 ({out7: 1, out4: 0}) \n'
    #         'G4 P.2 \n'
    #         # open main gate
    #         'M100 ({out3: 1}) \n'
    #         'G4 P.2 \n'
    #         # push forward
    #         'M100 ({out6: 1}) \n'
    #         'G4 P.6 \n'
    #         # close main gate again and close sub-gate
    #         'M100 ({out3: 0, out4: 1}) \n'
    #         'G4 P.2 \n'
    #         # bring up finger
    #         'M100 ({out7: 0}) \n'
    #         'G4 P.2 \n'
    #         # bring pusher back
    #         'M100 ({out6: 0}) \n'
    #         'G4 P1.5 \n'
    #     )
    #
    # await feeder.set_valves([0] * 14)

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
