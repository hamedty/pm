import time

from machine import Machine
from vision import Detector

m = Machine()
d = Detector()


m.send_command(home=1)
input('place dosing and holder correctly')
m.send_command(v2=1, v4=1, m4=43000)
time.sleep(.2)
m.send_command(v2=1, v4=1, v1=1)

# vision align

while True:
    d_h = d.detect_holder()
    if (abs(d_h) < 3):
        break
    m3 = d_h / 100.0 * 200 * 32
    m.send_command(v1=1, v2=1, v4=1, m3=m3)


m.send_command(v1=1, v2=1)
time.sleep(.2)

m.send_command(v1=1, v2=1, m4=2800)
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

m.send_command(v1=1, m4=-40000)
time.sleep(.2)

m.send_command()
