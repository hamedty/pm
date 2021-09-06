import importlib
import os
import json
import asyncio
import time
import subprocess
import threading

import traceback
from arduino import Arduino
from camera import cheap_cam, vision
import rpi_scripts
global ARDUINOS, CAMERAS
MAX_ARDUINO_COUNT = 5
ARDUINOS = {}
CAMERAS = {}

DATA_PATH = '/home/pi/data'


async def create_camera(command, _):
    if 'holder' not in CAMERAS:
        CAMERAS['holder'] = cheap_cam.create_camera(
            'holder', command['holder_roi'])
    if 'dosing' not in CAMERAS:
        CAMERAS['dosing'] = cheap_cam.create_camera(
            'dosing', command['dosing_roi'])
    return {'success': True}


async def dump_frame(command, _):
    CAMERAS['holder'].dump_frame(
        filename=DATA_PATH + '/holder.png', roi_index=command.get('roi_index_holder'))
    CAMERAS['dosing'].dump_frame(
        filename=DATA_PATH + '/dosing.png', roi_index=command.get('roi_index_dosing'))
    return {'success': True}


async def dump_training(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    component = command['component']  # holder / dosing
    feed = command['speed']
    camera = CAMERAS[component]
    axis = {'holder': 'X', 'dosing': 'Y'}[component]

    os.system('rm -rf %s/*' % DATA_PATH)
    directory = os.path.join(DATA_PATH, command['folder_name'])
    os.makedirs(directory)

    no_frames = command['revs'] * command['frames_per_rev']
    steps = 360.0 / command['frames_per_rev']
    if component == 'dosing':
        steps = -steps

    webcam_buffer_length = 4
    for frame_no in range(-webcam_buffer_length, no_frames):
        if frame_no < 0:
            filename = None  # capture frame but ignore buffer
        else:
            seq = frame_no % command['frames_per_rev']
            round = int(frame_no / command['frames_per_rev'])
            # save file
            filename = '%s/%03d_%02d.png' % (directory, seq, round)
        camera.dump_frame(filename=filename, pre_fetch=0)

        if (frame_no + webcam_buffer_length) < no_frames:
            await asyncio.sleep(.033)  # wait for one frame to scan
            arduino.send_command('G10 L20 P1 %s0' % axis)
            arduino.send_command('G1 %s%.02f F%d' % (axis, steps, feed))
            command_id = arduino.get_command_id()
            arduino.send_command('N%d M0' % (command_id))
            await arduino.wait_for_command_id(command_id)

            delay = .25
            await asyncio.sleep(delay)  # needed for system to settle

    return {'success': True}


async def align(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    component = command['component']  # holder / dosing
    camera = CAMERAS[component]
    axis = {'holder': 'X', 'dosing': 'Y'}[component]
    valve = {'holder': 'out2', 'dosing': 'out1'}[component]
    detector = {'holder': vision.detect_holder,
                'dosing': vision.detect_dosing}[component]
    presence_threshold = {'holder': 70, 'dosing': 50}[component]
    retries = command['retries']
    offset = arduino._hw_config.get(component + '_offset', 0)
    feed = command['speed']
    steps_history = []

    aligned = False
    exists = False
    for i in range(retries):
        frame = camera.get_frame(roi_index=0)
        if i == 0:  # check existance for the first time
            frame2 = camera.get_frame(pre_fetch=-1, roi_index=1)
            if not vision.object_present(frame2, presence_threshold):
                break
            exists = True
        steps, aligned = detector(frame, offset)
        print(steps, aligned)
        steps_history.append(steps)
        if aligned:
            break

        arduino.send_command('G10 L20 P1 %s0' % axis)
        arduino.send_command('G1 %s%d F%d' % (axis, steps, feed))
        await asyncio.sleep(abs(steps) / float(feed) * 60 + .1)

    arduino.send_command(json.dumps({valve: 0}))
    return {'success': True, 'aligned': aligned, 'exists': exists, 'steps_history': steps_history}


async def create_arduino(command, _):
    arduino_index = command['arduino_index']
    if ARDUINOS.get(arduino_index) is None:
        arduino = Arduino(arduino_index)
        arduino.receive_thread = threading.Thread(
            target=arduino._receive)
        arduino.receive_thread.start()
        ARDUINOS[arduino_index] = arduino
    return {'success': True}


async def restart_arduino(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    arduino.restart()
    return {'success': True}


async def config_arduino(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    arduino._hw_config = command['hw_config']
    for key, value in command['g2core_config']:
        command_id = arduino.send_command(json.dumps({key: value}))
    importlib.reload(rpi_scripts)
    return {'success': True}


async def raw(command, _):
    arduino = ARDUINOS[command['arduino_index']]

    wait_start = command['wait_start']
    wait_completion = command['wait_completion']
    command_raw = command['data']

    if wait_start:
        await arduino.wait_for_status(wait_list=wait_start)

    if wait_completion:
        command_id = arduino.get_command_id()
        command_raw = command_raw + '\nN%d M0' % command_id

    arduino.send_command(command_raw)

    if wait_completion:
        await arduino.wait_for_command_id(command_id)

    status = arduino.get_status()

    if status['f.2'] != 0:
        return {'success': False, 'message': 'firmware status failed', 'status': status}

    return {'success': True, 'status': status}


async def G1(command, _):
    correction_eps = 0.5
    arduino = ARDUINOS[command['arduino_index']]
    arduino._debug = True
    for a in ['x', 'y', 'z']:
        if command.get(a) is not None:
            axes = a
            req_location = command[a]
            break
    feed = command['feed']
    wait_start = {1, 3, 4}
    retries = 10
    # check current position is correct
    result, g2core_location, encoder_location = arduino.check_encoder(axes)
    print(result, g2core_location, encoder_location)
    if not result:
        arduino._debug = False
        return {'success': False, 'message': 'current position is incorrect g2core %.2f encoder %.2f' % (g2core_location, encoder_location)}

    for r in range(retries):
        # command move
        command_id = arduino.get_command_id()
        command_raw = 'G1 %s%.2f F%d\nN%d M0' % (
            axes, req_location, feed, command_id)

        if abs(g2core_location - encoder_location) > correction_eps:
            command_raw = 'G28.3 %s%.03f\n' % (
                axes, encoder_location) + command_raw
        arduino.send_command(command_raw)
        await arduino.wait_for_command_id(command_id)

        # if encoder pos is correct return success
        result, g2core_location, encoder_location = arduino.check_encoder(axes)
        print(result, g2core_location, encoder_location)

        if result:
            arduino._debug = False
            return {'success': True, 'status': arduino.get_status()}

        # get latest position
        await asyncio.sleep(.2)
        command_id = arduino.get_command_id()
        command_raw = '{pos%s:n}\nN%d M0' % (axes, command_id)
        arduino.send_command(command_raw)
        await arduino.wait_for_command_id(command_id)

        # update position
        result, g2core_location, encoder_location = arduino.check_encoder(axes)
        command_id = arduino.get_command_id()
        command_raw = 'G28.3 %s%.03f\nN%d M0' % (
            axes, encoder_location, command_id)
        arduino.send_command(command_raw)
        await arduino.wait_for_command_id(command_id)
        feed = .85 * feed

    arduino._debug = False
    return {'success': False, 'message': 'Failed after many retries - g2core %.2f encoder %.2f' % (g2core_location, encoder_location)}


async def G1_w_assert(*args, **kwargs):
    res = await G1(*args, **kwargs)
    assert res['success'], res


async def feeder_process(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    await rpi_scripts.feeder_process(arduino, G1_w_assert, command)
    return {'success': True}


async def status_hook(command, writer):
    arduino_index = command['arduino_index']

    while ARDUINOS.get(arduino_index) is None:
        await asyncio.sleep(0.25)
        status = {'message': 'arduino not created'}
        response = json.dumps(status) + '\n'
        writer.write(response.encode())
        if writer.is_closing():
            return {}
    arduino = ARDUINOS[arduino_index]
    status_queue = asyncio.Queue()
    arduino._status_out_queue = status_queue

    while True:
        try:
            status = await asyncio.wait_for(status_queue.get(), timeout=.5)
        except asyncio.TimeoutError:
            arduino.send_command('{stat:n}')
            continue
        status_queue.task_done()
        response = json.dumps(status) + '\n'
        writer.write(response.encode())
        if writer.is_closing():
            return {}


COMMAND_HANDLER = {
    # vision
    'create_camera': create_camera,
    'dump_frame': dump_frame,
    'dump_training': dump_training,

    'align': align,

    # hardware
    'create_arduino': create_arduino,
    'config_arduino': config_arduino,
    'raw': raw,
    'G1': G1,
    'feeder_process': feeder_process,
    'restart_arduino': restart_arduino,

    # second channel - status
    'status_hook': status_hook,
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
            response = await COMMAND_HANDLER[data['verb']](data, writer)
        except:
            trace = traceback.format_exc()
            print(trace)
            response = {'success': False, 'message': traceback.format_exc()}

        # print('response', response)
        response = json.dumps(response) + '\n'

        if writer.is_closing():
            return
        writer.write(response.encode())


async def async_main():
    server = await asyncio.start_server(
        server_handler, '0.0.0.0', 2000)
    print('starting server')
    async with server:
        await server.serve_forever()


def main():
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
