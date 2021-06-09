import os
import json
import asyncio
import time
import subprocess
import threading
# import multiprocessing as mp
import traceback
from arduino import Arduino
from camera import cheap_cam, vision
import arduino_constants as _

global ARDUINOS, CAMERAS
MAX_ARDUINO_COUNT = 5
ARDUINOS = [None] * 6
CAMERAS = {}

DATA_PATH = '/home/pi/data'


async def create_camera(command):
    if 'holder' not in CAMERAS:
        CAMERAS['holder'] = cheap_cam.create_camera(
            'holder', command['holder_roi'])
    if 'dosing' not in CAMERAS:
        CAMERAS['dosing'] = cheap_cam.create_camera(
            'dosing', command['dosing_roi'])
    return {'success': True}


async def dump_frame(command):
    CAMERAS['holder'].dump_frame(
        filename=DATA_PATH + '/holder.png', roi_index=command.get('roi_index_holder'))
    CAMERAS['dosing'].dump_frame(
        filename=DATA_PATH + '/dosing.png', roi_index=command.get('roi_index_dosing'))
    return {'success': True}


async def dump_training_holder(command):
    if (CAMERAS['holder'] is None) or (CAMERAS['dosing'] is None):
        return {'success': False, 'message': 'cameras not created'}
    arduino = ARDUINOS[0]

    os.system('rm -rf %s/*' % DATA_PATH)
    directory = os.path.join(DATA_PATH, command['folder_name'])
    os.makedirs(directory)

    no_frames = command['revs'] * command['frames_per_rev']
    steps = int(command['step_per_rev'] / command['frames_per_rev'])
    # step_delay = 250

    webcam_buffer_length = 4
    for frame_no in range(-webcam_buffer_length, no_frames):
        if frame_no < 0:
            filename = None  # capture frame but ignore buffer
        else:
            seq = frame_no % command['frames_per_rev']
            round = int(frame_no / command['frames_per_rev'])
            # save file
            filename = '%s/%03d_%02d.png' % (directory, seq, round)
        CAMERAS['holder'].dump_frame(filename=filename, pre_fetch=0)

        if (frame_no + webcam_buffer_length) < no_frames:
            await asyncio.sleep(.033)  # wait for one frame to scan
            arduino.move_motors([{'steps': steps, 'delay': 250}])
            delay = abs(steps) * 250 * 2 * 1e-6 + .25
            await asyncio.sleep(delay)  # needed for system to settle

    return {'success': True}


async def dump_training_dosing(command):
    arduino = ARDUINOS[0]

    os.system('rm -rf %s/*' % DATA_PATH)
    directory = os.path.join(DATA_PATH, command['folder_name'])
    os.makedirs(directory)

    no_frames = command['revs'] * command['frames_per_rev']
    steps = int(command['step_per_rev'] / command['frames_per_rev'])
    # step_delay = 250

    webcam_buffer_length = 4
    for frame_no in range(-webcam_buffer_length, no_frames):
        if frame_no < 0:
            filename = None  # capture frame but ignore buffer
        else:
            seq = frame_no % command['frames_per_rev']
            round = int(frame_no / command['frames_per_rev'])
            # save file
            filename = '%s/%03d_%02d.png' % (directory, seq, round)
        CAMERAS['dosing'].dump_frame(filename=filename, pre_fetch=0)

        if (frame_no + webcam_buffer_length) < no_frames:
            await asyncio.sleep(.033)  # wait for one frame to scan
            arduino.move_motors([{}, {}, {'steps': -steps, 'delay': 250}])
            delay = abs(steps) * 250 * 2 * 1e-6 + .25
            await asyncio.sleep(delay)  # needed for system to settle

    return {'success': True}


async def align(command):
    arduino = ARDUINOS[0]
    component = command['component']  # holder / dosing
    camera = CAMERAS[component]
    axis = {'holder': 'X', 'dosing': 'Y'}[component]
    valve = {'holder': 'out2', 'dosing': 'out1'}[component]
    detector = {'holder': vision.detect_holder,
                'dosing': vision.detect_dosing}[component]
    feed = command['speed']

    arduino.send_command(json.dumps({valve: 1}))
    await asyncio.sleep(.5)

    for i in range(20):
        frame = camera.get_frame(roi_index=0)
        steps, aligned = detector(frame)
        print(steps, aligned)
        if aligned:
            break

        arduino.send_command('G10 L20 P1 %s0' % axis)
        arduino.send_command('G1 %s%d F%d' % (axis, steps, feed))

        waaaait

    arduino.send_command(json.dumps({valve: 0}))
    return {'success': aligned}


async def create_arduino(command):
    usb_index = command.get('arduino_index', None)
    arduino_index = command.get('arduino_index', 0)
    if ARDUINOS[arduino_index] is not None:
        return {'success': True, 'message': 'already created'}

    arduino = Arduino(usb_index)
    arduino.receive_thread = threading.Thread(target=arduino._receive)
    arduino.receive_thread.start()

    ARDUINOS[arduino_index] = arduino
    return {'success': True}


async def config_arduino(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    arduino._hw_config = command['hw_config']
    for key, value in command['g2core_config']:
        command_id = arduino.send_command(json.dumps({key: value}))
    return {'success': True}


async def raw(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]

    wait = command.get('wait', False)
    if wait:
        await arduino.wait_for_status()
        arduino._status['stat'] = -1
    print(command)
    arduino.send_command(command['data'])

    if wait:
        await arduino.wait_for_status()

    return {'success': True, 'status': arduino.get_status()}


async def get_status(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    if arduino is None:
        status = {'message': 'arduino not created'}
    else:
        arduino.send_command('$')
        status = arduino.get_status()
    return {'success': True, 'status': status}

COMMAND_HANDLER = {
    # vision
    'create_camera': create_camera,
    'dump_frame': dump_frame,
    'dump_training_holder': dump_training_holder,
    'dump_training_dosing': dump_training_dosing,

    'align': align,

    # hardware
    'create_arduino': create_arduino,
    'config_arduino': config_arduino,
    'raw': raw,
    'get_status': get_status,
}


async def server_handler(reader, writer):
    while True:
        if reader.at_eof():
            writer.close()
            return
        data = await reader.readline()
        if not data:
            continue

        try:
            data = json.loads(data.decode())
            # print('command:', data)
            response = await COMMAND_HANDLER[data['verb']](data)
        except:
            trace = traceback.format_exc()
            print(trace)
            response = {'success': False, 'message': traceback.format_exc()}

        # print('response', response)
        response = json.dumps(response) + '\n'

        writer.write(response.encode())


async def async_main():
    server = await asyncio.start_server(
        server_handler, '0.0.0.0', 2000)
    print('starting server')
    async with server:
        await server.serve_forever()


def main():
    # mp.set_start_method('spawn')
    # q = mp.Queue()
    # p = mp.Process(target=foo, args=(q,))
    # p.start()
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
