import asyncio
import subprocess


async def f1(q):
    while True:
        q.put_nowait('a')
        await asyncio.sleep(.1)


async def main():
    q = asyncio.Queue()
    t1 = asyncio.create_task(f1(q))

    while True:
        try:
            a = await asyncio.wait_for(q.get(), timeout=.5)
            print(1, a)
        except asyncio.TimeoutError:
            print(2)


asyncio.run(main())
