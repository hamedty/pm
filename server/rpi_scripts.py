import asyncio
import time
import random

HOLDER_ARDUINO_INDEX = 2


'''
    m1 (10): holder sequencer - on and off (jack)
    m2, m3: holder pusher motors
    m4, m7: holder elevator and conveyor
    m5, m9: dosing feeder motors
    m6, m8: reserve

    out1: holder microswitch lock
    out2: comb
    out3: reserve (used as M1 - not connected electrically)
    out4: push cartridge to vaccum
    out5: reserve
    out6: hug
    out7: holder gate
    out8: reserve
    out9: cartridge lift
    out10: air pusher
    out11: dosing gate
    out12: reserve (broken solonoid)
    out13: cartridge vaccum
    out14: reserve
'''


async def feeder_process(arduino, G1, command):
    FEEDER_OFFSET = command['z_offset']
    FEED_FEED = command['feed_feed']
    JERK_FEED = command['jerk_feed']
    JERK_IDLE = command['jerk_idle']
    CARTRIDGE_FEED = command['cartridge_feed']

    # prepare masks
    holder_mask = command['holder_mask']
    dosing_mask = command['dosing_mask']
    assert len(holder_mask) == len(dosing_mask)
    N = len(holder_mask)
    holder_mask.append(0)
    dosing_mask.append(0)

    # initial condition
    initial_z = FEEDER_OFFSET
    arduino._send_command('''
        {out2: 1}
        {z:{jm:%d}}
        ''' % JERK_FEED)

    # Motors
    if any(dosing_mask):
        arduino._send_command("{m5: 25, m9: 5}")

    arduino._send_command("{m2: 4, m3: 4, out10: 1}")

    holder_shift_register = 0
    dosing_gate_status = 0

    for i in range(N):
        # Gate Open
        if holder_mask[i]:
            arduino._send_command("{out7: 1, m2: 4, m3: 4}")
        if dosing_mask[i] and not dosing_gate_status:
            arduino._send_command("{out11: 1}")
            dosing_gate_status = 1

        # Wait for holder
        current_z = FEEDER_OFFSET + 25 * i
        await wait_for_inputs(arduino, holder_mask[i], dosing_mask[i], current_z)

        # Close Gate
        if not dosing_mask[i + 1] and dosing_gate_status:
            arduino._send_command("{out11: 0}")
            dosing_gate_status = 0

        # Grab
        if CARTRIDGE_FEED and any(holder_mask[i:]):
            await cartridge_grab(arduino)

        # Move and Handover
        z = FEEDER_OFFSET + 25 * (i + 1)
        if CARTRIDGE_FEED:
            await move_rail_n_cartridge_handover(arduino, z, FEED_FEED, G1)
            await asyncio.sleep(.1)  # vaccum release
        else:
            await G1({'arduino_index': HOLDER_ARDUINO_INDEX, 'z': z, 'feed': FEED_FEED, 'correct_initial': True})
            arduino.send_command('{out1: 0}')
            await asyncio.sleep(.1)  # wait to release microswitch holder

    arduino._send_command('G1 Y10 F60000')
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
    await G1({'arduino_index': HOLDER_ARDUINO_INDEX, 'z': z, 'feed': feed, 'correct_initial': True})

    command_id = arduino.get_command_id()
    command_raw = '''
        ; release microswitch holder
        M100 ({out1: 0})

        ; hug
        M100 ({out6: 1})

        ; put in cartridge
        G38.2 Y-100 F2000
        M100 ({clear:n})
        ; vaccum release
        M100 ({out13: 0})
        G10 L20 P1 Y0

        ; un-hug
        M100 ({out6: 0})
        N%d M0
        ''' % command_id
    arduino.send_command(command_raw)
    await arduino.wait_for_command_id(command_id)


async def wait_for_inputs(arduino, holder, dosing, current_z):
    print('waiting for holder')
    if holder:
        value = False
        while not value:
            _, value = await arduino.read_metric('in5', 'r.in5')
    print('holder done')

    arduino._send_command('{out7: 0, m2: 30, m3: 30}')
    await asyncio.sleep(.2)
    arduino._send_command('{out1: 1}')

    print('waiting for dosing')
    if dosing:
        value = False
        while not value:
            _, value = await arduino.read_metric('in6', 'r.in6')
    print('dosing done')
