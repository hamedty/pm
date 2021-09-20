import asyncio
import time


async def feeder_process(arduino, G1, command):
    FEEDER_OFFSET = command['z_offset']
    FEED_FEED = command['feed_feed']
    JERK_FEED = command['jerk_feed']
    FEED_COMEBACK = command['feed_comeback']
    JERK_COMEBACK = command['jerk_comeback']
    JERK_IDLE = command['jerk_idle']

    holder_mask = command['mask']
    N = len(holder_mask)
    holder_mask.append(0)

    initial_z = FEEDER_OFFSET
    arduino._send_command("{m2: 2, m3: 4}")
    arduino._send_command("{out2: 0}")
    arduino._send_command('{z:{jm:%d}}' % JERK_COMEBACK)
    await G1({'arduino_index': None, 'z': initial_z, 'feed': FEED_COMEBACK})
    arduino._send_command("{out2: 1}")
    arduino._send_command('{z:{jm:%d}}' % JERK_FEED)

    holder_shift_register = 0
    gate_status = 0

    for i in range(N):
        # Gate Open
        if holder_mask[i] and not gate_status:
            arduino._send_command("{out7: 1}")
            gate_status = 1

        # Grab
        if any(holder_mask[i:]):
            await cartridge_grab(arduino)

        Wait for holder
        if holder_mask[i]:
            await detect_holder_wraper(arduino)

        # Close Gate
        if not holder_mask[i + 1] and gate_status:
            arduino._send_command("{out7: 0}")
            gate_status = 0

        # Move and Handover
        z = FEEDER_OFFSET + 25 * (i + 1)
        await move_rail_n_cartridge_handover(arduino, z, FEED_FEED, G1)

        if int(i / 1) % 2:
            arduino._send_command("{m2: 4, m3: 2}")
        else:
            arduino._send_command("{m2: 2, m3: 4}")
    arduino._send_command('{z:{jm:%d}}' % JERK_IDLE)


async def cartridge_grab(arduino):
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
    arduino._send_command("{out9: 0}")  # bring jack up and open hug
    await asyncio.sleep(.1)

    # Cartridge Pusher back
    arduino._send_command("{out4: 0}")  # pull cartridge pusher back
    await asyncio.sleep(.02)


async def move_rail_n_cartridge_handover(arduino, z, feed, G1):
    # rotate to rail
    # arduino._send_command("G1 Y10 F25000")
    command_id = arduino.get_command_id()
    arduino._send_command('''
        G1 Y10 Z%.2f F26000
        M100 ({posz:n})
        N%d M0
        ''' % (z, command_id))
    await arduino.wait_for_command_id(command_id)
    await asyncio.sleep(.6)
    await G1({'arduino_index': None, 'z': z, 'feed': feed, 'correct_initial': True})

    command_id = arduino.get_command_id()
    command_raw = '''
        M100 ({out8: 1})
        G38.2 Y-100 F2000
        M100 ({clear:n})
        M100 ({out13: 0})
        G10 L20 P1 Y0
        M100 ({out8: 0})
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
