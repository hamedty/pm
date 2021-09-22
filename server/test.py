import asyncio
import subprocess


async def f2():
    print('f2 in')
    await asyncio.sleep(1)
    print('f2 out')


async def f1():
    while True:
        print('f2 start')
        await asyncio.shield(f2())
        print('f2 done')


async def main():
    z = asyncio.create_task(f1())
    await asyncio.sleep(5.3)
    z.cancel()
    await asyncio.sleep(2)

asyncio.run(main())
