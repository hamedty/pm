import asyncio

from node import ALL_NODES

N = len(ALL_NODES)
CHECK_GREEN = '\033[92m✓\033[0m'
CROSS_RED = '\033[91m✖\033[0m'


async def call_all_wrapper(func, timeout=None):
    result = await asyncio.gather(*[asyncio.wait_for(func(node), timeout=timeout) for node in ALL_NODES], return_exceptions=True)
    for i in range(N):
        print('\t%s: ' % ALL_NODES[i].ip, end='')
        if result[i] == True:
            print(CHECK_GREEN)
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
    result = await call_all_wrapper(lambda x: x.connect(), timeout=1)
    assert(all(result))

    # reset arduino
    # print('reseting arduino ...')
    # result = await call_all_wrapper(lambda x: x.send_command_reset_arduino(), timeout=5)
    # assert(all(result))

    # hardware config
    print('config arduino ...')
    result = await call_all_wrapper(lambda x: x.send_command_config_arduino(), timeout=200)
    assert(all(result))

    # # set valves
    # print('set valves ...')
    # command = {
    #     'verb': 'set_valves',
    #     'valves': [0, 1],
    # }
    #
    # def func(x): return x.send_command(command)
    # result = await call_all_wrapper(func, timeout=2)
    # assert(all(result))

    # # move motors
    # command = {
    #     'verb': 'move_motors',
    #     'moves': [[0, 200, 1], [5000, 500, 1]],
    # }
    #
    # def func(x): return x.send_command(command)
    # result = await call_all_wrapper(func, timeout=10)
    # assert(all(result))

    # home motors
    command = {
        'verb': 'home',
        'axis': 1,
    }

    def func(x): return x.send_command(command)
    result = await call_all_wrapper(func, timeout=30)
    assert(all(result))

asyncio.run(main())

# asyncio.run(ALL_NODES[0].send_command(
#     {'verb': 'move_motors', 'moves': [[00, 200, 1], [-500, 200, 1]], }))
# asyncio.run(n.send_command({'verb': 'set_valves', 'valves': [1, 1]], }))
