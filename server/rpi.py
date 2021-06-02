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
        CAMERAS['holder'] = cheap_cam.create_camera('holder')
    if 'dosing' not in CAMERAS:
        CAMERAS['dosing'] = cheap_cam.create_camera('dosing')
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

    if component == 'dosing':
        valves = [1]
        detector = vision.detect_dosing
    else:
        valves = [None, 1]
        detector = vision.detect_holder

    arduino.set_valves(valves)
    await asyncio.sleep(.5)

    while True:
        frame = camera.get_frame(roi_index=0)
        steps, aligned = detector(frame)
        print(steps, aligned)
        if aligned:
            break

        if component == 'dosing':
            arduino.move_motors(
                [{}, {}, {'steps': int(steps), 'delay': 250, 'blocking': 1}])
        else:
            arduino.move_motors(
                [{'steps': int(steps), 'delay': 250, 'blocking': 1}])

        delay = abs(steps) * 250 * 2 * 1e-6 + .2
        await asyncio.sleep(delay)  # needed for system to settle

    arduino.set_valves([0, 0])
    return {'success': True}


async def get_status(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    if arduino is None:
        status = {'message': 'arduino not created'}
    else:
        status = arduino.get_status()
    return {'success': True, 'status': status}


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


async def reset_arduino(command):
    c = ['raspi-gpio', 'set', str(command['pin']), 'dl']
    await asyncio.sleep(.1)

    subprocess.call(c, stdout=subprocess.PIPE)
    await asyncio.sleep(.2)

    c[3] = 'dh'
    subprocess.call(c, stdout=subprocess.PIPE)
    await asyncio.sleep(2)

    for arduino in ARDUINOS:
        if arduino is not None:
            arduino._open_port()
    return {'success': True}


async def config_arduino(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    arduino.define_valves(command['hw_config']['valves'])
    arduino.define_di(command['hw_config'].get('di', []))
    for motor_no, motor in enumerate(command['hw_config']['motors']):
        motor['motor_no'] = motor_no
        arduino.define_motor(motor)

    return {'success': True}


async def set_valves(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    arduino.set_valves(command['valves'])
    return {'success': True}


async def move_motors(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    command_id, motor_moves_clean = arduino.move_motors(command['moves'])
    while not arduino.fence[command_id]:
        await asyncio.sleep(.002)
    response = arduino.fence[command_id]
    del arduino.fence[command_id]

    success = True
    message = ''

    for motor_index in range(len(motor_moves_clean)):  # for every motor in command
        motor_move = motor_moves_clean[motor_index]
        enabled = motor_move['flags'] & _.MOVE_MOTOR_FLAGS_ENABLED
        if not enabled:
            continue
        absolute = motor_move['flags'] & _.MOVE_MOTOR_FLAGS_ABSOLUTE
        if not absolute:
            continue

        # motor_moves = [{telorance_soft, telorance_hard}, ...]
        has_encoder = arduino._hw_config['motors'][motor_index]['has_encoder']
        encoder_no = arduino._hw_config['motors'][motor_index]['encoder_no']

        if not has_encoder:
            success = False
            message += 'Motor Index: %d, Message: %s\n' % (
                motor_index, 'Absolute move requested while motor has no encoder')
            continue

        current_position = response['encoders'][encoder_no]
        requested_position = motor_move['steps']
        diversion = abs(requested_position - current_position)
        telorance_soft = motor_move['telorance_soft']
        if diversion >= telorance_soft:
            success = False
            message += 'Motor Index: %d, Message: %s\n' % (
                motor_index, 'error is above soft threashold')

    return {'success': success, 'message': message}


async def home(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    command_id = arduino.home(command['axis'])
    while not arduino.fence[command_id]:
        await asyncio.sleep(.002)
    response = arduino.fence[command_id]
    del arduino.fence[command_id]
    motor_status = response['motor_status'][command['axis']]
    success = (motor_status == _.MOTOR_STATUS_DEFINED)
    return {'success': success, 'message': 'Motor Status: %d' % motor_status}


async def define_trajectory(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    arduino.define_trajectory(command['data'])
    return {'success': True}

COMMAND_HANDLER = {
    # vision
    'create_camera': create_camera,
    'dump_frame': dump_frame,
    'dump_training_holder': dump_training_holder,
    'dump_training_dosing': dump_training_dosing,

    'align': align,

    # hardware
    'get_status': get_status,
    'create_arduino': create_arduino,
    'reset_arduino': reset_arduino,
    'config_arduino': config_arduino,
    'set_valves': set_valves,
    'move_motors': move_motors,
    'home': home,

    # trajectory
    'define_trajectory': define_trajectory,
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
