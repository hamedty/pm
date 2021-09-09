import asyncio
import subprocess


async def f1():
    pass
    print(1)


async def main():
    t1 = asyncio.create_task(f1())
    await t1
    await t1


asyncio.run(main())
