import json
import asyncio
import subprocess
import traceback


async def reset_arduino(command):
    c = ['gpio', str(command['pin']), 'dl']
    subprocess.call(c, stdout=subprocess.PIPE)
    await asyncio.sleep(.5)
    c[2] = 'dh'
    subprocess.call(c, stdout=subprocess.PIPE)

    return {'success': True}


async def config_arduino(command):
    print(command)

    return {'success': True}


COMMAND_HANDLER = {
    'reset_arduino': reset_arduino,
    'config_arduino': config_arduino,
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
            response = await COMMAND_HANDLER[data['verb']](data)
        except:
            response = {'success': False, 'traceback': traceback.print_exc()}

        response = json.dumps(response) + '\n'

        writer.write(response.encode())


async def main():
    server = await asyncio.start_server(
        server_handler, '0.0.0.0', 2000)

    async with server:
        await server.serve_forever()

asyncio.run(main())
