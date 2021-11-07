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
global PEN_ID
PEN_ID = 0
ARDUINOS = {}
CAMERAS = {}

DATA_PATH = '/home/pi/data'


async def dump_frame(command, _):
    arduino.send_command('{out6:1}')

    CAMERAS['holder'].dump_frame(
        filename=DATA_PATH + '/holder.png', roi_name=command.get('roi_index_holder'))
    CAMERAS['dosing'].dump_frame(
        filename=DATA_PATH + '/dosing.png', roi_name=command.get('roi_index_dosing'))
    return {'success': True}

    arduino.send_command('{out6:0}')


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
    arduino.send_command('{out6:1}')

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

    arduino.send_command('{out6:0}')
    return {'success': True}


async def align(command, _):

    arduino = ARDUINOS[command['arduino_index']]
    component = command['component']  # holder / dosing
    camera = CAMERAS[component]
    axis = {'holder': 'X', 'dosing': 'Y'}[component]
    valve = {'holder': 'out2', 'dosing': 'out1'}[component]
    detector = {'holder': vision.detect_holder,
                'dosing': vision.detect_dosing}[component]

    arduino.send_command('{out6:1}')

    global PEN_ID
    if PEN_ID > 10:
        os.system('rm /home/pi/data/%04d_*' % PEN_ID)

    presence_threshold = arduino._hw_config['presence_threshold'][component]
    retries = command['retries']
    offset = arduino._hw_config.get(component + '_offset', 0)
    feed = command['speed']
    steps_history = []

    aligned = False
    for j in range(3):
        arduino.send_command('{%s:1}' % valve)
        await asyncio.sleep(.05)

        for i in range(retries):
            frame = camera.get_frame(roi_name='alignment')

            # filename = '/home/pi/data/%04d_%s_%d.png' % (PEN_ID, component, i)
            # vision.dump(frame, filename)

            steps, aligned = detector(frame, offset)
            # print(steps, aligned)
            steps_history.append(steps)
            if aligned:
                break

            arduino.send_command('G10 L20 P1 %s0' % axis)
            arduino.send_command('G1 %s%d F%d' % (axis, steps, feed))
            await asyncio.sleep(abs(steps) / float(feed) * 60 + .1)

        arduino.send_command('{%s:0}' % valve)

        if component == 'holder' and aligned:
            await asyncio.sleep(.25)
            frame = camera.get_frame(roi_name='alignment')
            _, aligned_check = detector(frame, offset)
            if aligned_check:
                break
        else:
            break

    if component == 'dosing':
        PEN_ID += 1

    arduino.send_command('{out6:0}')
    return {'success': True, 'aligned': aligned, 'steps_history': steps_history}


async def detect_vision(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    object = command['object']

    arduino.send_command('{out6:1}')

    if object == 'dosing_sit_right':
        camera = CAMERAS['dosing']
        roi_name = 'sit_right'
        pre_fetch = camera.DEFAULT_PRE_FETCH
        frame = camera.get_frame(pre_fetch=pre_fetch, roi_name=roi_name)
        result = vision.dosing_sit_right(
            frame, arduino._hw_config['dosing_sit_right'])
    elif object == 'no_holder_no_dosing':
        frames = await asyncio.gather(
            CAMERAS['dosing'].async_get_frame(
                pre_fetch=CAMERAS['dosing'].DEFAULT_PRE_FETCH, roi_name='existance'),
            CAMERAS['holder'].async_get_frame(
                pre_fetch=CAMERAS['holder'].DEFAULT_PRE_FETCH, roi_name='existance')
        )
        result = frames[0]
        dosing_present, dosing_value = vision.object_present(
            frames[0], arduino._hw_config['presence_threshold']['dosing'])
        holder_present, holder_value = vision.object_present(
            frames[1], arduino._hw_config['presence_threshold']['holder'])
        result = {
            'dosing_present': dosing_present,
            'dosing_value': dosing_value,
            'holder_present': holder_present,
            'holder_value': holder_value,
            'no_dosing': not dosing_present,
            'no_holder': not holder_present,
            'no_holder_no_dosing': not (dosing_present or holder_present),
        }
    else:
        arduino.send_command('{out6:0}')
        return {'success': False, 'message': 'Unknown object to detect'}

    arduino.send_command('{out6:0}')
    result['success'] = True
    return result


async def restart_arduino(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    arduino.restart()
    return {'success': True}


async def create_arduino(command, _):
    arduino_index = command['arduino_index']
    # create arduino
    if ARDUINOS.get(arduino_index) is None:
        arduino = Arduino(arduino_index)
        arduino.receive_thread = threading.Thread(
            target=arduino._receive)
        arduino.receive_thread.start()
        ARDUINOS[arduino_index] = arduino
    arduino = ARDUINOS[command['arduino_index']]

    # reload scripts
    importlib.reload(rpi_scripts)

    # config arduino & G2
    arduino._hw_config = command['hw_config']
    for key, value in command['g2core_config']:
        command_id = arduino.send_command(json.dumps({key: value}))

    # create cameras
    for cam_id in arduino._hw_config.get('cameras', {}):  # holder, dosing, etc
        if cam_id not in CAMERAS:
            rois = arduino._hw_config['cameras'][cam_id]['rois']
            CAMERAS[cam_id] = cheap_cam.create_camera(cam_id, rois)

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


async def G1(command, _=None):
    correction_eps = 0.5
    arduino = ARDUINOS[command['arduino_index']]
    for a in ['x', 'y', 'z']:
        if command.get(a) is not None:
            axes = a
            req_location = command[a]
            break
    feed = command['feed']
    correct_initial = command.get('correct_initial', False)
    retries = 3

    # needed for accurate location and encoder
    await arduino.wait_for_status(wait_list={1, 3, 4})

    # check current position is correct
    result, reached, g2core_location, encoder_location = arduino.check_encoder(
        axes, req_location, check_telorance_hard=(not correct_initial))
    print('check_encoder1:', result, reached,
          g2core_location, encoder_location)
    if (not correct_initial) and (not result):
        return {'success': False, 'message': 'current position is incorrect g2core %.2f encoder %.2f' % (g2core_location, encoder_location)}
    if reached:
        return {'success': True, 'status': arduino.get_status()}

    for r in range(retries):
        # command move
        command_raw = ''
        if abs(g2core_location - encoder_location) > correction_eps:
            command_raw += 'G28.3 %s%.03f\n' % (axes, encoder_location)

        command_raw += 'G1 %s%.2f F%d\n' % (axes, req_location, feed)
        command_id = arduino.get_command_id()
        command_raw += 'N%d M0' % command_id

        arduino.send_command(command_raw)
        await arduino.wait_for_command_id(command_id)
        print('send_command1:', command_raw)
        # if encoder pos is correct return success
        result, reached, g2core_location, encoder_location = arduino.check_encoder(
            axes, req_location)
        print('check_encoder2:', result, reached,
              g2core_location, encoder_location)
        if result:
            return {'success': True, 'status': arduino.get_status()}

        # get latest position
        # await asyncio.sleep(.2)
        command_id = arduino.get_command_id()
        command_raw = '{pos%s:n}\nN%d M0' % (axes, command_id)
        arduino.send_command(command_raw)
        print('send_command2:', command_raw)
        await arduino.wait_for_command_id(command_id)

        # update position
        correction_eps = 0
        feed = .8 * feed

    return {'success': False, 'message': 'Failed after many retries - g2core %.2f encoder %.2f' % (g2core_location, encoder_location)}


async def G1_w_assert(*args, **kwargs):
    res = await G1(*args, **kwargs)
    assert res['success'], res


async def feeder_process(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    await rpi_scripts.feeder_process(arduino, G1_w_assert, command)
    return {'success': True}


async def read_metric(command, _):
    arduino = ARDUINOS[command['arduino_index']]
    query = command['query']
    response = command['response']
    success, result = await arduino.read_metric(query, response)
    return {'success': success, 'result': result}


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
    'dump_frame': dump_frame,
    'dump_training': dump_training,

    'align': align,
    'detect_vision': detect_vision,

    # hardware
    'restart_arduino': restart_arduino,
    'create_arduino': create_arduino,
    'raw': raw,
    'G1': G1,
    'feeder_process': feeder_process,
    'read_metric': read_metric,

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
