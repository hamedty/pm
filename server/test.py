import asyncio
import aioconsole
import inspect


class HW_PANIC_EXCEPTION(Exception):
    pass


async def f(t, i):
    await asyncio.sleep(t)
    print(i)


async def main():
    await gather(f(1, 1))


async def gather(a):
    print(1111)
    if callable(a):
        print()
        if inspect.isawaitable(a):
            await a
        else:
            a()
    elif isinstance(a, list):
        for i in a:
            await gather(i)
    elif isinstance(a, set):
        await asyncio.gather(*[gather(i) for i in a])

asyncio.run(main())
