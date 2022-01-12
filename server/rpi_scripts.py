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
    # 0- parse input params

    FEEDER_OFFSET = command['z_offset']
    FEED_COMEBACK = command['feed_comeback']
    FEED_FEED = command['feed_feed']
    JERK_FEED = command['jerk_feed']
    JERK_IDLE = command['jerk_idle']
    CARTRIDGE_FEED = command['cartridge_feed']

    # prepare masks
    initial_z = FEEDER_OFFSET
    N = len(command['mask'])
    mask = command['mask'] + [0]

    #---------------------------------------------------------------

    # 1- initial condition
    # a- holder motors on, cartridge fast, air pusher on, comb back
    arduino._send_command(f'''
        {{m2: 4, m3: 4, m6: 15}}
        {{out2:0, out10: 1}}
        ''')

    # b- G1 to location
    await G1({'arduino_index': HOLDER_ARDUINO_INDEX, 'z': initial_z, 'feed': FEED_COMEBACK, 'correct_initial': True})

    # c- comb forward, dosing gate / and High jerk active
    arduino._send_command(f'''
        {{out2: 1}}
        {{out11: 1}}
        {{z:{{jm: {JERK_FEED:.0f}}}}}
        ''')
    #---------------------------------------------------------------
    # 2- loop

    # # dosing gate
    # dosing_gate = 0
    # if mask[0] and dosing_gate == 0:
    #     arduino._send_command('{out11: 1}')
    #     dosing_gate = 1

    holder_task = asyncio.create_task(do_holder_task(-1, N, mask, arduino))
    for i in range(N):
        await holder_task

        # # close dosing gate
        # if (mask[i + 1] == 0) and (dosing_gate == 1):
        #     arduino._send_command('{out11: 0}')
        #     dosing_gate = 0
        #     await asyncio.sleep(.25)

        z = FEEDER_OFFSET + 25 * (i + 1)
        await mover_rail_n_grab(arduino, z, FEED_FEED, G1)

        # # open dosing gate
        # if mask[i + 1] and (dosing_gate == 0):
        #     arduino._send_command('{out11: 1}')
        #     dosing_gate = 1

        holder_task = asyncio.create_task(do_holder_task(i, N, mask, arduino))
        await place_cartridge(arduino)
    await holder_task

    #---------------------------------------------------------------
    # 3- relax condition
    arduino._send_command(f'''
        {{z:{{jm: {JERK_IDLE:.0f}}}}}
        G1 Y10 F60000
        {{m2: 30, m3: 30, m6: 100}}
        {{out10: 1}}
        ''')


async def do_holder_task(n, N, mask, arduino):
    await wait_for_inputs(arduino, holder_mask=1, holder_value=0)
    n += 2  # 1 indexed holder number
    if n <= N:
        arduino._send_command("{out7: 1}")  # gate will be closed automatically
        await asyncio.sleep(0.05)
        await wait_for_inputs(arduino, holder_mask=1, dosing_mask=1)
    if n == N:
        # close dosing gate
        arduino._send_command("{out11: 0}")
    if n > N:
        # release holder microswitch
        arduino._send_command("{out1: 0}")


async def mover_rail_n_grab(arduino, z, feed, G1):
    command_id = arduino.get_command_id()
    arduino._send_command(f"G1 Y101 Z{z:.1f} F55000")
    await asyncio.sleep(.006 * 5)
    arduino._send_command(f'''
        {{out9: 1, out13: 1}}
        M100 ({{posz:n}})
        M100 ({{uda0:"0x{command_id:x}"}})
    ''')
    await arduino.wait_for_command_id(command_id)
    await G1({'arduino_index': HOLDER_ARDUINO_INDEX, 'z': z, 'feed': feed, 'correct_initial': True})

    # cartridge forward / hug / release holder microswitch
    arduino._send_command("{out4: 1, out6: 1, out1: 0}")
    await asyncio.sleep(.15)


async def place_cartridge(arduino):
    # bring jack up
    arduino._send_command("{out9: 0}")  # bring jack up
    await asyncio.sleep(.07)

    # rotate to rail
    arduino._send_command('G1 Y.5 F35000')

    await asyncio.sleep(.04)
    arduino._send_command("{out4: 0}")  # cartridge pusher back
    await asyncio.sleep(.25)
    arduino._send_command("{ out13: 0}")  # vaccum release
    await asyncio.sleep(.1)
    arduino._send_command("{out6: 0}")  # unhug


async def wait_for_inputs(arduino, holder_mask=0, dosing_mask=0, holder_value=1, dosing_value=1):
    if holder_mask:
        value = False
        while True:
            _, read_value = await arduino.read_metric('in5', 'r.in5')
            value = (read_value == holder_value)
            if value:
                break
            await asyncio.sleep(0.005)

    if dosing_mask:
        value = False
        if dosing_value:
            while arduino.dosing_reserve < 5:
                await asyncio.sleep(0.001)
        while True:
            _, read_value = await arduino.read_metric('in6', 'r.in6')
            value = (read_value == dosing_value)
            if value:
                break
            await asyncio.sleep(0.005)
        if dosing_value:
            await arduino.set_dosing_reserve(change=-1)
