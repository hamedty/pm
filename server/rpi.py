import json
import asyncio
import subprocess
import traceback
from arduino import Arduino

print('start Arduino')
arduino = Arduino()


async def reset_arduino(command):
    c = ['raspi-gpio', 'set', str(command['pin']), 'dl']
    await asyncio.sleep(.1)

    subprocess.call(c, stdout=subprocess.PIPE)
    await asyncio.sleep(.2)

    c[3] = 'dh'
    subprocess.call(c, stdout=subprocess.PIPE)
    await asyncio.sleep(2)

    arduino._open_port()
    return {'success': True}


async def config_arduino(command):
    arduino.define_valves(command['hw_config']['valves'])
    for motor_no, motor in enumerate(command['hw_config']['motors']):
        motor['motor_no'] = motor_no
        arduino.define_motor(motor)

    return {'success': True}


async def set_valves(command):
    arduino.set_valves(command['valves'])
    return {'success': True}


async def move_motors(command):
    arduino.move_motors(command['moves'])
    return {'success': True}


async def home(command):
    arduino.home(command['axis'])
    return {'success': True}

COMMAND_HANDLER = {
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
