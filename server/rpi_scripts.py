import asyncio
import time
import random

HOLDER_ARDUINO_INDEX = 2


'''
    m1 (10): holder sequencer - on and off (jack)
    m2, m3: holder pusher motors
    m4: holder conveyor
    m5, m9: dosing feeder motors
    m6: cartridge conveyor
    m7: holder elevator
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

    in1: X (cartridge feeder arm 1) home switch
    in2: Y (cartridge feeder arm 2) home switch
    in3: Z (main axis) home switch
    in4: holder air low level optical sensor
    in5: holder microswitch
    in6: dosing existance sensor
    in7(s2): Cartridge Hug sensor
    in8: holder air high level optical sensor
    in9: low cartridge alarm - NC - active low

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
    mask_holder = command['mask'] + [0]
    mask_dosing = command['mask'] + [0, 0]

    disabled_stations = [2, 6]
    for disabled_station in disabled_stations:
        holder_index = (disabled_station + 2) % 10
        dosing_index = (disabled_station + 6) % 10
        mask_holder[holder_index] = 0  # station 2 - 4
        mask_dosing[dosing_index] = 0  # station 2 - 8

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
        {{eac1:3500}}
        {{out2: 1}}
        {{out11: 1}}
        {{z:{{jm: {JERK_FEED:.0f}}}}}
        ''')
    #---------------------------------------------------------------
    # 2- loop

    for i in range(N + 1):
        holder_task = asyncio.create_task(do_holder_task(
            i, N, mask_holder, mask_dosing, arduino))

        if i != 0:
            await place_cartridge(arduino, mask_cartridge=mask_holder[i - 1])

        await holder_task

        if i == N:
            break

        z = FEEDER_OFFSET + 25 * (i + 1)
        await mover_rail_n_grab(arduino, z, FEED_FEED, G1, mask_cartridge=mask_holder[i])

    #---------------------------------------------------------------
    # 3- relax condition
    arduino._send_command(f'''
        {{eac1:600}}
        {{z:{{jm: {JERK_IDLE:.0f}}}}}
        G1 Y10 F60000
        {{m2: 30, m3: 30, m6: 70}}
        {{out1: 0, out10: 1}}
        ''')


async def do_holder_task(i, N, mask_holder, mask_dosing, arduino):
    ''' This function get called 11 times. When the rail is at the exact location'''

    # open dosing gate
    if (mask_dosing[i] == 1) and (i == 0 or (mask_dosing[i - 1] == 0)):
        arduino._send_command('{out11: 1}')

    # no holder before gate and holder Q is full
    await wait_for_inputs(arduino,
                          holder_mask=1,
                          holder_value=0,
                          holder_line_mask=1)

    if i < N:
        # gate will be closed automatically
        arduino._send_command(f"{{out7: {mask_holder[i]:d}}}")
        await asyncio.sleep(0.05)
        await wait_for_inputs(arduino,
                              holder_mask=mask_holder[i],
                              dosing_mask=mask_dosing[i])

    # close dosing gate
    if (mask_dosing[i + 1] == 0) and (mask_dosing[i] == 1):
        arduino._send_command('{out11: 0}')
        await asyncio.sleep(.1)


async def mover_rail_n_grab(arduino, z, feed, G1, mask_cartridge):
    command_id = arduino.get_command_id()
    arduino._send_command(f"G1 Y101 Z{z:.1f} F55000")
    await asyncio.sleep(.006 * 5)
    arduino._send_command(f'''
        {{uda1:"0x0"}}
        {{out9: 1, out13: {mask_cartridge}}}

        ;release holder microswitch
        M100 ({{posz:n, out1: 0}})
        M100 ({{uda0:"0x{command_id:x}"}})
    ''')
    await arduino.wait_for_command_id(command_id)
    await G1({'arduino_index': HOLDER_ARDUINO_INDEX, 'z': z, 'feed': feed, 'correct_initial': True})

    # cartridge forward / hug
    arduino._send_command(f"{{out4: {mask_cartridge:d}, out6: 1}}")


async def place_cartridge(arduino, mask_cartridge):
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

    if mask_cartridge:
        await wait_for_cartridge(arduino)


async def wait_for_cartridge(arduino):
    if arduino._status.get('r.uda1', 0) == 1:
        return

    # arduino.errors.append('no_cartridge')
    while not arduino._status.get('r.uda1', 0):
        await asyncio.sleep(.1)


async def wait_for_inputs(arduino,
                          holder_mask=0,
                          holder_value=1,
                          holder_line_mask=0,
                          dosing_mask=0,
                          dosing_value=1):
    if holder_mask:
        while True:
            _, read_value = await arduino.read_metric('in5', 'r.in5')
            value = (read_value == holder_value)
            if value:
                break
            await asyncio.sleep(0.005)
        # if holder_value:
        #     await wait_for_input(arduino, 'in5', lambda x: x == 1, 0.005, 'no_holder_at_gate')
        # else:
        #     await wait_for_input(arduino, 'in5', lambda x: x == 0, 0.005, 'extra_holder_at_gate')

    if holder_line_mask:
        while True:
            _, read_value = await arduino.read_metric('uda2', 'r.uda2')
            if read_value < 20000:
                break
            await asyncio.sleep(0.005)
        # await wait_for_input(arduino, 'uda2', lambda x: x < 20000, 0.005, 'not_enough_holder')

    if dosing_mask:
        if dosing_value:
            while arduino.dosing_reserve < 6:
                await asyncio.sleep(0.001)
        while True:
            _, read_value = await arduino.read_metric('in6', 'r.in6')
            value = (read_value == dosing_value)
            if value:
                break
            await asyncio.sleep(0.005)
        if dosing_value:
            await arduino.set_dosing_reserve(change=-1)


async def wait_for_input(arduino, metric, checker, delay, error_id):
    n = 0
    error_registered = False
    while True:
        _, read_value = await arduino.read_metric(metric)
        if checker(read_value):
            break
        n += 1
        if n * delay > 1 and not error_registered:
            error_registered = True
            asyncio.create_task(register_error(error_id))
        await asyncio.sleep(delay)

    if error_registered:
        asyncio.create_task(clear_error(error_id))


async def register_error(error_id):
    pass


async def clear_error(error_id):
    pass
