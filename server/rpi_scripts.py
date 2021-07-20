import asyncio
import time


async def feeder_process(arduino, G1):
    t0 = time.time()

    holder_lock = asyncio.Lock()
    holder_lock_rail = asyncio.Lock()
    cartridge_lock = asyncio.Lock()
    cartridge_lock_rail = asyncio.Lock()

    for i in range(12):
        # rail must be stationary
        t1 = t2 = None
        if 10 >= i >= 1:
            t1 = asyncio.create_task(holder_handover(arduino, holder_lock))
        if 11 >= i >= 2:
            t2 = asyncio.create_task(
                cartridge_handover(arduino, cartridge_lock))
        await asyncio.sleep(.05)

        # rail can move
        if 9 >= i >= 0:
            asyncio.create_task(holder_feed(arduino, holder_lock))
        if 10 >= i >= 1:
            asyncio.create_task(cartridge_feed(arduino, cartridge_lock))

        t1 is None or await t1
        t2 is None or await t2
        if 10 >= i >= 1:
            await move_rail(arduino, G1, i)
        else:
            await asyncio.sleep(.05)

    print(time.time() - t0)

    res = await G1({'arduino_index': None, 'z': 718, 'feed': 6000}, None)
    assert res['success']
    # input('handover?')
    res = await G1({'arduino_index': None, 'z': 16, 'feed': 6000}, None)
    assert res['success']
    print(time.time() - t0)


async def move_rail(arduino, G1, index):
    await asyncio.sleep(.05)
    z = index * 25 + 16
    print('going to Z:%d' % z)
    res = await G1({'arduino_index': None, 'z': z, 'feed': 6000}, None)
    assert res['success']
    # arduino._send_command("G1 Z%d F6000" % z)
    # await asyncio.sleep(0.6)


async def holder_feed(arduino, holder_lock):
    async with holder_lock:
        # H::6 - bring pusher back
        arduino._send_command("{out6: 0}")
        await asyncio.sleep(1.5)

        # H::1 bring finger down (7) and open sub-gate(4)
        arduino._send_command("{out7: 1, out8: 1, out4: 0, out5: 0}")
        await asyncio.sleep(.2)

        # H::2 - open main gate
        arduino._send_command("{out3: 1}")
        await asyncio.sleep(.2)

        # H::3 - push forward
        arduino._send_command("{out6: 1}")
        await asyncio.sleep(.6)


async def holder_handover(arduino, holder_lock):
    async with holder_lock:
        # H::4 - close main gate again and close sub-gate
        arduino._send_command("{out3: 0, out4: 1, out5: 1}")
        await asyncio.sleep(.2)

        # H::5 - bring up finger
        arduino._send_command("{out7: 0, out8: 0}")
        await asyncio.sleep(.2)


async def cartridge_feed(arduino, cartridge_lock):
    async with cartridge_lock:
        # rotate to upstream
        arduino._send_command("G1 X180 Y180 F100000")
        await asyncio.sleep(.3)

        # bring jack down
        arduino._send_command("{out9: 1, out10: 1}")
        await asyncio.sleep(.2)

        # turn on vacuum
        arduino._send_command("{out13: 1, out14: 1}")
        await asyncio.sleep(.2)

        # bring jack down
        arduino._send_command("{out9: 0, out10: 0}")
        await asyncio.sleep(.2)

        # rotate to mid air
        arduino._send_command("G1 X90 Y90 F50000")
        await asyncio.sleep(.05)

        # take jack up
        arduino._send_command("{out9: 1, out10: 1}")
        await asyncio.sleep(.4)


async def cartridge_handover(arduino, cartridge_lock):
    async with cartridge_lock:
        # rotate to rail
        arduino._send_command("G1 X5 Y5 F50000")
        await asyncio.sleep(.05)
        #
        # # take jack up
        # arduino._send_command("{out9: 1}")
        # await asyncio.sleep(.4)

        # bring jack down
        arduino._send_command("{out9: 0, out10: 0}")
        await asyncio.sleep(.2)

        # release vacuum
        arduino._send_command("{out13: 0, out14: 0}")
        await asyncio.sleep(.2)
