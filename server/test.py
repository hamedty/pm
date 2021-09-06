import asyncio
import subprocess


async def scp_to(path_src, path_dst):
    command = 'rsync -az %s pi@%s:%s' % (path_src, '192.168.44.101', path_dst)
    print(command)
    proc = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    print(stdout)
    print(stderr)
    assert proc.returncode == 0, proc.returncode


async def main():
    await scp_to('./rpi_scripts.py', '~/server/')


asyncio.run(main())
