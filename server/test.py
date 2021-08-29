import asyncio


class HW_PANIC_EXCEPTION(Exception):
    pass


async def f1():
    await asyncio.sleep(1)
    raise


async def f2():
    await asyncio.sleep(1)


async def main():
    # Create an Event object.
    # lock = asyncio.Lock()

    # Spawn a Task to wait until 'event' is set.
    # producer_task = asyncio.create_task(producer(lock))
    # waiter_task = asyncio.create_task(waiter(lock))

    # Sleep for 1 second and set the event.
    # await waiter_task
    # await producer_task
    # raise HW_PANIC_EXCEPTION('asdasd')
    await asyncio.gather(f1(), f2())


asyncio.run(main())
