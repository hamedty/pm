import asyncio
import time
import random


async def feeder_process(arduino, G1, command):
    FEEDER_OFFSET = command['z_offset']
    FEED_FEED = command['feed_feed']
    JERK_FEED = command['jerk_feed']
    JERK_IDLE = command['jerk_idle']
    CARTRIDGE_FEED = command['cartridge_feed']

    holder_mask = command['mask']
    N = len(holder_mask)
    holder_mask.append(0)

    initial_z = FEEDER_OFFSET
    arduino._send_command('''
        {out2: 1}
        {z:{jm:%d}}
        ''' % JERK_FEED)
    oscillate_motors_task = asyncio.create_task(oscillate_motors(arduino))

    holder_shift_register = 0
    gate_status = 0

    for i in range(N):
        # Gate Open
        if holder_mask[i] and not gate_status:
            arduino._send_command("{out7: 1}")
            gate_status = 1

        # Grab
        if CARTRIDGE_FEED and any(holder_mask[i:]):
            await cartridge_grab(arduino)

        # Wait for holder
        if holder_mask[i]:
            await detect_holder_wraper(arduino)

        # Close Gate
        if not holder_mask[i + 1] and gate_status:
            arduino._send_command("{out7: 0}")
            gate_status = 0

        # Move and Handover
        z = FEEDER_OFFSET + 25 * (i + 1)
        if CARTRIDGE_FEED:
            await move_rail_n_cartridge_handover(arduino, z, FEED_FEED, G1)
            await asyncio.sleep(.1)  # vaccum release
        else:
            await G1({'arduino_index': None, 'z': z, 'feed': FEED_FEED})

    arduino._send_command('{z:{jm:%d}}' % JERK_IDLE)
    oscillate_motors_task.cancel()


async def oscillate_motors(arduino):
    async def send_command_to_be_shielded(arduino, command):
        arduino._send_command(command)
    m2 = 4
    m3 = 2
    dir = 1
    while True:
        command = "{m2: %d, m3: %d}" % (m2, m3)
        await asyncio.shield(send_command_to_be_shielded(arduino, command))
        await asyncio.sleep(.3 + 0.3 * random.random())
        if m2 == 4 or m3 == 4:
            dir = -dir
        m2 += dir
        m3 -= dir


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
        await asyncio.sleep(0.002)
    return arduino._status['r.in5']
