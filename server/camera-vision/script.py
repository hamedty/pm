import time

from machine import Machine
from vision import Detector

m = Machine()
d = Detector()

while True:
    m.send_command(home=1)
    input('place dosing and holder correctly')
    m.send_command(v2=1, v4=1, m4=21500)
    time.sleep(.2)
    m.send_command(v2=1, v4=1, v1=1)

    # vision align

    while True:
        _, steps_holder, aligned_holder = d.detect_holder()
        if (aligned_holder):
            break
        m.send_command(v1=1, v2=1, v4=1, m3=steps_holder)

    while True:
        _, steps_dosing, aligned_dosing = d.detect_dosing()
        print(_)
        if (aligned_dosing):
            break
        m.send_command(v1=1, v2=1, v4=1, m1=steps_dosing)

    # input('aligned')
    # m.send_command(v4=1)
    # m.send_command(v4=1, m4=-20000)
    # time.sleep(.5)

    m.send_command(v1=1, v2=1)
    time.sleep(.2)

    m.send_command(v1=1, v2=1, m4=1400)
    time.sleep(.2)

    m.send_command(v1=1, v2=1, m1=6400 * -.9)
    time.sleep(.2)

    m.send_command(v1=1, v2=1, v5=1)
    time.sleep(.2)

    # verify microswitch here

    m.send_command(v5=1)
    time.sleep(.2)

    m.send_command(v5=1, v3=1)
    time.sleep(.7)

    m.send_command(v5=1)
    time.sleep(.2)

    # press finished
    m.send_command(v1=1)
    time.sleep(.2)

    m.send_command(v1=1, dance=.9)
    time.sleep(.2)

    m.send_command(v1=1, m4=-20000)
    time.sleep(.2)

    m.send_command()
