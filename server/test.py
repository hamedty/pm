import asyncio
import subprocess


async def main():
    a = True
    if a:
        print('true')
        a = False
    else:
        print('false')

asyncio.run(main())
