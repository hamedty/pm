import asyncio
import time
import random

HOLDER_ARDUINO_INDEX = 2


'''
    m1 (10): holder sequencer - on and off (jack)
    m2, m3: holder pusher motors
    m4: holder elevator
    m5, m9: dosing feeder motors
    m6: cartridge conveyor
    m7: holder conveyor
    m8: cartridge randomizer

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

    in1:
    in2:
    in3:
    in4:
    in5: holder microswitch
    in6: dosing existance sensor
'''


async def feeder_process(arduino, G1, command):
    FEEDER_OFFSET = command['z_offset']
    FEED_COMEBACK = command['feed_comeback']
    FEED_FEED = command['feed_feed']
    JERK_FEED = command['jerk_feed']
    JERK_IDLE = command['jerk_idle']
    CARTRIDGE_FEED = command['cartridge_feed']

    # prepare masks
    initial_z = FEEDER_OFFSET
    holder_mask = command['holder_mask']
    dosing_mask = command['dosing_mask']
    assert len(holder_mask) == len(dosing_mask)
    N = len(holder_mask)
    holder_mask.append(0)
    dosing_mask.append(0)

    # 1- initial condition
    # a- holder motors on, cartridge fast, air pusher on
    arduino._send_command("{m2: 4, m3: 4, m6: 15}")
    arduino._send_command("{out2:0, out10: 1}")
    await G1({'arduino_index': HOLDER_ARDUINO_INDEX, 'z': initial_z, 'feed': FEED_COMEBACK, 'correct_initial': True})

    arduino._send_command(f'''
        {{out2: 1}}
        {{z:{{jm: {JERK_FEED:.0f}}}}}
        ''')

    dosing_gate_status = 0

    for i in range(N):
        # 1- holder feed
        # holder shouldn't exists before gate
        await wait_for_inputs(arduino, holder_mask=1, holder_value=0)
        # Gate Open
        if holder_mask[i]:
            # holder motors and gate. Firmware automatically closes the gate
            arduino._send_command("{out7: 1}")

        if dosing_mask[i] and not dosing_gate_status:
            arduino._send_command("{out11: 1}")  # dosing gate
            dosing_gate_status = 1

        # Grab
        if CARTRIDGE_FEED and any(holder_mask[i:]):
            await cartridge_grab(arduino)

        # Wait for holder
        await wait_for_inputs(arduino, holder_mask=holder_mask[i], dosing_mask=dosing_mask[i])

        # Close Dosing Gate
        if not dosing_mask[i + 1] and dosing_gate_status:
            arduino._send_command("{out11: 0}")
            dosing_gate_status = 0

        # Move and Handover
        z = FEEDER_OFFSET + 25 * (i + 1)
        if CARTRIDGE_FEED:
            await move_rail_n_cartridge_handover(arduino, z, FEED_FEED, G1)
            await asyncio.sleep(.1)  # vaccum release
        else:
            await G1({'arduino_index': HOLDER_ARDUINO_INDEX, 'z': z, 'feed': FEED_FEED, 'correct_initial': True})
            arduino.send_command('{out1: 0}')
            await asyncio.sleep(.1)  # wait to release microswitch holder

    arduino._send_command("{m2: 30, m3: 30, m6: 100}")

    arduino._send_command('G1 Y10 F60000')
    arduino._send_command('{z:{jm:%d}}' % JERK_IDLE)


async def cartridge_grab(arduino):
    # rotate to upstream + Vacuum + bring jack down
    arduino._send_command("{out9: 1}")
    arduino._send_command('''
        G1 Y101 F60000
        M100.1 ({out13: 1})
        ''')
    await asyncio.sleep(.24)

    # Cartridge Pusher
    arduino._send_command("{out4: 1}")  # push cartridge forward
    await asyncio.sleep(.02)

    # bring jack up
    arduino._send_command("{out9: 0}")  # bring jack up and open hug
    await asyncio.sleep(.1)


async def move_rail_n_cartridge_handover(arduino, z, feed, G1):
    # rotate to rail
    command_id = arduino.get_command_id()
    arduino._send_command('''
        G1 Y10 Z%.2f F35000
        M100 ({posz:n})
        M100 ({uda0:"0x%x"})
        ''' % (z, command_id))
    await arduino.wait_for_command_id(command_id)

    await G1({'arduino_index': HOLDER_ARDUINO_INDEX, 'z': z, 'feed': feed, 'correct_initial': True})

    command_id = arduino.get_command_id()
    command_raw = '''
        ; out1: release microswitch holder / out4: pull cartridge pusher back / out6: hug
        M100 ({out:{1:0,4:0,6:1}})

        ; put in cartridge
        G38.2 Y-100 F2000
        M100 ({clear:n})
        ; vaccum release
        M100 ({out13: 0})
        G10 L20 P1 Y0

        ; un-hug
        M100 ({out6: 0})
        M100 ({uda0:"0x%x"})
        ''' % command_id
    arduino.send_command(command_raw)
    await arduino.wait_for_command_id(command_id)


async def wait_for_inputs(arduino, holder_mask=0, dosing_mask=0, holder_value=1, dosing_value=1):
    # print('waiting for holder')
    if holder_mask:
        value = False
        while not value:
            _, read_value = await arduino.read_metric('in5', 'r.in5')
            value = (read_value == holder_value)

    # print('waiting for dosing')
    if dosing_mask:
        value = False
        while not value:
            _, read_value = await arduino.read_metric('in6', 'r.in6')
            value = (read_value == dosing_value)
    # print('dosing done')
