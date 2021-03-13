import time

from machine import Machine
# import vision

m = Machine()
# d = vision.Detector()
SA_DANCE = 400 * 11. / 8.

while True:
    # # Home
    m.bootup()

    # align0
    # while True:
    #     sd = 0  # d.detect_dosing()
    #     sh = d.detect_holder()
    #     print(sd, sh)
    #     # input('?')
    #     if (abs(sh) < 10) and (min(sd, 400 - sd) < 10):
    #         break
    #     m.send_command(vd=1, vh=1, sd=int(sd), sh=int(sh))
    # m.send_command(vd=1, vh=1, sd=0, sh=sh)

    time.sleep(0.25)

    # come down
    m.send_command(vd=1, sa=2300)
    # input()
    time.sleep(0.5)
    m.send_command(vd=1, sd=-400)
    # input()

    time.sleep(0.5)
    m.send_command(vd=1, vdn=1)
    # input()

    time.sleep(0.5)
    m.send_command(vd=1, vdn=1, dance=-1)
    # input()

    time.sleep(0.25)

    # press
    m.send_command(vdn=1)

    time.sleep(0.25)
    m.send_command(vdn=1, vp=1)

    time.sleep(0.5)
    m.send_command(vdn=1)
    time.sleep(0.25)
    m.send_command()
    time.sleep(0.25)
    m.send_command(vd=1)
    time.sleep(0.25)
    m.send_command(vd=1, sa=-2500)
    m.send_command(vdc=1, vd=1)
    time.sleep(0.25)
    m.send_command(vdc=1, vd=1, dance=2)
    m.send_command(vd=1)
    time.sleep(0.25)
    m.send_command(vd=1, sa=-6000)
    input('take it')
    m.send_command()
    time.sleep(0.25)
