import asyncio
import time


async def feeder_process(arduino, G1, command):
    FEEDER_OFFSET = 17
    FEED = 7000
    holder_mask = command['mask']
    N = len(holder_mask)
    holder_mask.append(0)

    initial_z = FEEDER_OFFSET
    arduino._send_command("{out2: 0}")
    await G1({'arduino_index': None, 'z': initial_z, 'feed': FEED})

    arduino._send_command("{out2: 1}")
    await asyncio.sleep(.3)

    holder_shift_register = 0
    gate_status = 0

    for i in range(N + 1):
        if not holder_mask[i] and gate_status:
            arduino._send_command("{out7: 0}")
            gate_status = 0

        z = FEEDER_OFFSET + 25 * i
        # if z != FEEDER_OFFSET:  # not in the first loop
        #     await G1({'arduino_index': None, 'z': z, 'feed': FEED})
        if i > 0:
            await cartridge_feed_n_move_rail(arduino, z, FEED, G1)

        if holder_mask[i] and not gate_status:
            # arduino._send_command("{out7: 1}")
            gate_status = 1

        if holder_shift_register:
            await cartridge_handover(arduino, None)

        # if int(i / 1) % 2:
        #     arduino._send_command("{m2: 4, m3: 2}")
        # else:
        #     arduino._send_command("{m2: 2, m3: 4}")
        if holder_mask[i]:
            holder_shift_register = True  # await detect_holder_wraper(arduino)


async def cartridge_feed_n_move_rail(arduino, z, z_FEED, G1):
    # rotate to upstream + Vacuum + bring jack down
    arduino._send_command("{out9: 1}")
    arduino._send_command('''
        G1 Y100 F60000
        M100.1 ({out13: 1})
        ''')
    await asyncio.sleep(.24)

    # Cartridge Pusher
    arduino._send_command("{out4: 1}")  # push cartridge forward
    await asyncio.sleep(.02)

    # bring jack up
    arduino._send_command("{out9: 0, out8:0}")  # bring jack up and open hug
    await asyncio.sleep(.1)

    # Cartridge Pusher back
    arduino._send_command("{out4: 0}")  # pull cartridge pusher back
    await asyncio.sleep(.02)

    # rotate to rail
    # arduino._send_command("G1 Y10 F25000")
    command_id = arduino.get_command_id()
    arduino._send_command('''
        G1 Y10 Z%.2f F26000
        N%d M0
        ''' % (z, command_id))
    await arduino.wait_for_command_id(command_id)
    await G1({'arduino_index': None, 'z': z, 'feed': z_FEED, 'correct_initial': True})
    # await asyncio.sleep(.5)


async def cartridge_handover(arduino, cartridge_lock):
    command_id = arduino.get_command_id()
    command_raw = '''
        M100 ({out8: 1})
        G38.2 Y-100 F2000
        M100 ({clear:n})
        M100 ({out13: 0})
        G10 L20 P1 Y0
        N%d M0
        ''' % command_id
    arduino.send_command(command_raw)
    await arduino.wait_for_command_id(command_id)


async def cartridge_repeat_home(arduino):
    command_id = arduino.get_command_id()
    command_raw = '''
        G1 Y20 F60000
        G38.3 Y-100 F1000
        G10 L20 P1 Y0
        N%d M0
        ''' % command_id
    arduino.send_command(command_raw)
    await arduino.wait_for_command_id(command_id)


async def detect_holder_wraper(arduino):
    value = False
    while not value:
        value = await detect_holder(arduino)
    return value


async def detect_holder(arduino):
    if 'r.in5' in arduino._status:
        del arduino._status['r.in5']
    arduino._send_command('{in5:n}')
    while 'r.in5' not in arduino._status:
        await asyncio.sleep(0.001)
    return arduino._status['r.in5']

''' Old lock based code'''
# async def feeder_process(arduino, G1):
#     t0 = time.time()
#
#     holder_lock = asyncio.Lock()
#     holder_lock_rail = asyncio.Lock()
#     cartridge_lock = asyncio.Lock()
#     cartridge_lock_rail = asyncio.Lock()
#
#     for i in range(12):
#         # rail must be stationary
#         t1 = t2 = None
#         if 10 >= i >= 1:
#             t1 = asyncio.create_task(holder_handover(arduino, holder_lock))
#         if 11 >= i >= 2:
#             t2 = asyncio.create_task(
#                 cartridge_handover(arduino, cartridge_lock))
#         await asyncio.sleep(.05)
#
#         # rail can move
#         if 9 >= i >= 0:
#             asyncio.create_task(holder_feed(arduino, holder_lock))
#         if 10 >= i >= 1:
#             asyncio.create_task(cartridge_feed(arduino, cartridge_lock))
#
#         t1 is None or await t1
#         t2 is None or await t2
#         if 10 >= i >= 1:
#             await move_rail(arduino, G1, i)
#         else:
#             await asyncio.sleep(.05)
#
#     print(time.time() - t0)
#
#     res = await G1({'arduino_index': None, 'z': 718, 'feed': 6000}, None)
#     assert res['success']
#     # input('handover?')
#     res = await G1({'arduino_index': None, 'z': 16, 'feed': 6000}, None)
#     assert res['success']
#     print(time.time() - t0)
#
#
# async def holder_handover(arduino, holder_lock):
#     async with holder_lock:
#         # H::4 - close main gate again and close sub-gate
#         arduino._send_command("{out3: 0, out4: 1, out5: 1}")
#         await asyncio.sleep(.2)
#
#         # H::5 - bring up finger
#         arduino._send_command("{out7: 0, out8: 0}")
#         await asyncio.sleep(.2)
#
#
