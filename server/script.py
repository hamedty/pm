from machine import Machine
import time
m = Machine()
SA_DANCE = 400 * 11. / 8.

# # Home
m.send_command(home=1)
#
# # comming down
m.send_command(vdc=1)
input('place dosing and holder')
m.send_command(sa=5950, vdc=1)
time.sleep(0.5)
m.send_command(vdc=1, vd=1)
time.sleep(0.3)
m.send_command(vd=1)

# align
z = 1
while z:
    z = input('align, 0 for done')
    try:
        z = int(z)
    except:
        z = 10
    m.send_command(vd=1, sd=z)


# come down
m.send_command(vd=1, sa=2300)
time.sleep(0.5)
m.send_command(vd=1, sd=-400)
time.sleep(0.5)
m.send_command(vd=1, vdn=1)
time.sleep(0.5)
m.send_command(vd=1, vdn=1, dance=-1)
time.sleep(0.5)

# press
m.send_command(vdn=1)
time.sleep(0.5)
m.send_command(vdn=1, vp=1)
time.sleep(0.5)
m.send_command(vdn=1)
time.sleep(0.5)
m.send_command()
time.sleep(0.5)
m.send_command(vd=1)
time.sleep(0.5)
m.send_command(vd=1, sa=-2500)
m.send_command(vdc=1, vd=1)
time.sleep(.5)
m.send_command(vdc=1, vd=1, dance=2)
m.send_command(vd=1)
time.sleep(.5)
m.send_command(vd=1, sa=-6000)
input('take it')
m.send_command()
time.sleep(0.5)
