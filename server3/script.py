import time

from machine import Machine
# import vision

m = Machine()


m.send_command(home=1)
m.send_command(v4=1)
input('place dosing and holder correctly')
m.send_command(v4=1, m4=43000)
m.send_command(v4=1, v1=1)
# vision align
m.send_command(v1=1)
m.send_command(v1=1, m4=2800)

m.send_command(v1=1, m1=6400 * -.9)


m.send_command(v1=1, v5=1)

# verify microswitch here

m.send_command(v5=1)
m.send_command(v5=1, v3=1)

m.send_command(v5=1)

# press finished
m.send_command(v1=1)
m.send_command(v1=1, dance=.9)
m.send_command(v1=1, m4=-40000)
m.send_command()
