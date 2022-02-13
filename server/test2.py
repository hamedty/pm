import asyncio


async def f1():
    await asyncio.sleep(.5)


async def f2():
    await asyncio.sleep(.5)
    try:
        raise
        pass
    finally:
        pass


async def main():
    res = await asyncio.gather(f1(), f2())
    print(res)
    for i in range(len(res)):
        if isinstance(res[i], Exception):
            print(i, res[i])

    print('done')

asyncio.run(main())
