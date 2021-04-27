import asyncio

from node import ALL_NODES

# ALL_NODES = [ALL_NODES[-1]]
N = len(ALL_NODES)
CHECK_GREEN = '\033[92m✓\033[0m'
CROSS_RED = '\033[91m✖\033[0m'


async def call_all_wrapper(func, timeout=None):
    result = await asyncio.gather(*[asyncio.wait_for(func(node), timeout=timeout) for node in ALL_NODES], return_exceptions=True)
    for i in range(N):
        print('\t%s: ' % ALL_NODES[i].ip, end='')
        if result[i] == True:
            print(CHECK_GREEN, repr(result[i]))
        else:
            print(CROSS_RED, repr(result[i]))
    return result


async def main():
    # Ping Nodes
    print('Ping nodes ...')
    result = await call_all_wrapper(lambda x: x.ping(), timeout=5)
    assert(all(result))

    # Connect to them
    print('Connecting to nodes ...')
    result = await call_all_wrapper(lambda x: x.connect(), timeout=10)
    assert(all(result))

    # create camera
    print('create webcam')
    command = {
        'verb': 'create_camera',
    }

    def func(x): return x.send_command(command)
    result = await call_all_wrapper(func, timeout=100)
    assert(all(result))

    # dump frame
    print('create webcam')
    command = {
        'verb': 'dump_frame',
    }

    def func(x): return x.send_command(command)
    result = await call_all_wrapper(func, timeout=100)
    assert(all(result))

    # copy files
    def func(x): return x.scp_from('~/data/dosing.png', './dump/dosing.png')
    result = await call_all_wrapper(func, timeout=100)
    assert(all(result))

    def func(x): return x.scp_from('~/data/holder.png', './dump/holder.png')
    result = await call_all_wrapper(func, timeout=100)
    assert(all(result))

asyncio.run(main())
