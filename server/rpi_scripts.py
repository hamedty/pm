import asyncio
import time


async def feeder_process(arduino):
    t0 = time.time()
    N = 10
    holder_lock = asyncio.Lock()
    holder_lock_rail = asyncio.Lock()
    cartridge_lock = asyncio.Lock()
    cartridge_lock_rail = asyncio.Lock()

    for i in range(N):
        # rail must be stationary
        t1 = asyncio.create_task(holder_handover(arduino, holder_lock))
        t2 = asyncio.create_task(cartridge_handover(arduino, cartridge_lock))
        await asyncio.sleep(.05)

        # rail can move
        asyncio.create_task(holder_feed(arduino, holder_lock))
        asyncio.create_task(cartridge_feed(arduino, cartridge_lock))

        await t1
        await t2
        await move_rail(arduino, i + 1)

    print((time.time() - t0) / N)
    for j in range(14):
        arduino._send_command("{out%d: 0}" % (j + 1))


async def move_rail(arduino, index):
    z = (index % 2) * 25 + 16
    arduino._send_command("G1 Z%d F6000" % z)
    await asyncio.sleep(0.6)


async def holder_feed(arduino, holder_lock):
    async with holder_lock:
        # H::6 - bring pusher back
        arduino._send_command("{out6: 0}")
        await asyncio.sleep(1.5)

        # H::1 bring finger down (7) and open sub-gate(4)
        arduino._send_command("{out7: 1, out4: 0}")
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
        arduino._send_command("{out3: 0, out4: 1}")
        await asyncio.sleep(.2)

        # H::5 - bring up finger
        arduino._send_command("{out7: 0}")
        await asyncio.sleep(.2)


async def cartridge_feed(arduino, cartridge_lock):
    async with cartridge_lock:
        # rotate to upstream
        arduino._send_command("G1 Y180 F100000")
        await asyncio.sleep(.3)

        # bring jack down
        arduino._send_command("{out9: 1}")
        await asyncio.sleep(.2)

        # turn on vacuum
        arduino._send_command("{out13: 1}")
        await asyncio.sleep(.2)

        # bring jack down
        arduino._send_command("{out9: 0}")
        await asyncio.sleep(.2)

        # rotate to mid air
        arduino._send_command("G1 Y90 F50000")
        await asyncio.sleep(.05)

        # take jack up
        arduino._send_command("{out9: 1}")
        await asyncio.sleep(.4)


async def cartridge_handover(arduino, cartridge_lock):
    async with cartridge_lock:
        # rotate to rail
        arduino._send_command("G1 Y10 F50000")
        await asyncio.sleep(.05)
        #
        # # take jack up
        # arduino._send_command("{out9: 1}")
        # await asyncio.sleep(.4)

        # bring jack down
        arduino._send_command("{out9: 0}")
        await asyncio.sleep(.2)

        # release vacuum
        arduino._send_command("{out13: 0}")
        await asyncio.sleep(.2)
