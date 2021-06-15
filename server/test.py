import asyncio


async def waiter(lock):
    while True:
        if not lock.locked():
            await asyncio.sleep(.001)
            continue
        print('... got it!')
        lock.release()


async def producer(lock):
    while True:
        input('print?')
        await lock.acquire()


async def main():
    # Create an Event object.
    lock = asyncio.Lock()

    # Spawn a Task to wait until 'event' is set.
    producer_task = asyncio.create_task(producer(lock))
    waiter_task = asyncio.create_task(waiter(lock))

    # Sleep for 1 second and set the event.
    await waiter_task
    await producer_task


asyncio.run(main())
