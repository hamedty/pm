import asyncio


def run_exclusively(func):
    async def wrapper(system, ALL_NODES):
        lock = system.running_script_lock
        try:
            await asyncio.wait_for(lock.acquire(), timeout=.1)
            system.running_script = func.__name__
            await func(system, ALL_NODES)
        except asyncio.TimeoutError:
            print('Script blocked by exclusive lock')
        finally:
            system.running_script = None
            lock.release()

    return wrapper
