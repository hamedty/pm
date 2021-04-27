import json
import asyncio
import subprocess
import traceback
from arduino import Arduino
from camera import cheap_cam

global ARDUINOS, CAMERAS
ARDUINOS = []
CAMERAS = {}


async def create_camera(command):
    global CAMERAS
    CAMERAS = {}
    CAMERAS['holder'] = cheap_cam.create_camera('holder')
    CAMERAS['dosing'] = cheap_cam.create_camera('dosing')
    return {'success': True}


async def dump_frame(command):
    global CAMERAS
    CAMERAS['holder'].dump_frame('holder')
    CAMERAS['dosing'].dump_frame('dosing')
    return {'success': True}


async def create_arduino(command):
    global ARDUINOS
    ARDUINOS = []
    N = command.get('arduino_count', 1)
    for i in range(N):
        a = Arduino()
        ARDUINOS.append(a)
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
        arduino._open_port()
    return {'success': True}


async def config_arduino(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    arduino.define_valves(command['hw_config']['valves'])
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
    arduino.move_motors(command['moves'])
    return {'success': True}


async def home(command):
    arduino = ARDUINOS[command.get('arduino_index', 0)]
    arduino.home(command['axis'])
    return {'success': True}

COMMAND_HANDLER = {
    # vision
    'create_camera': create_camera,
    'dump_frame': dump_frame,

    # hardware
    'create_arduino': create_arduino,
    'reset_arduino': reset_arduino,
    'config_arduino': config_arduino,
    'set_valves': set_valves,
    'move_motors': move_motors,
    'home': home,
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
            print(data)
            response = await COMMAND_HANDLER[data['verb']](data)
        except:
            response = {'success': False, 'traceback': traceback.print_exc()}

        print(response)
        response = json.dumps(response) + '\n'

        writer.write(response.encode())


async def main():
    server = await asyncio.start_server(
        server_handler, '0.0.0.0', 2000)
    print('starting server')
    async with server:
        await server.serve_forever()

asyncio.run(main())
