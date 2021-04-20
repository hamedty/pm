shopt -s expand_aliases

alias python=python3
alias pip=pip3
cd ~/Desktop/PAM2060/firmware/

alias ssh-1="ssh pi@192.168.44.50"
alias fw-upload='scp /home/it/Desktop/PAM2060/firmware/.pio/build/due/firmware.bin  pi@192.168.44.50:~/ && ssh-1 "./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"'
alias srv-upload='scp -r /home/it/Desktop/PAM2060/server3/ pi@192.168.44.50:~/'

#
# cd motion_planning/
# python curve.py
# cd ../
#
# rm .pio/build/due/firmware.*
# pio run
# fw-upload
# sleep .3
ssh-1 'python3 server3/machine.py -home 1'
ssh-1 'time python3 server3/machine.py -m4 20000'
sleep .3
ssh-1 'time python3 server3/machine.py -m4 -20000'
sleep .3
ssh-1 'python3 server3/machine.py -home 1'
