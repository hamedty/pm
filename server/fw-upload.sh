scp /home/it/Desktop/PAM2060/firmware/.pio/build/due/firmware.bin  pi@192.168.44.51:~/
ssh pi@192.168.44.51 "./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"

# scp /home/it/Desktop/PAM2060/firmware/.pio/build/due/firmware.bin  pi@192.168.44.52:~/
# ssh pi@192.168.44.52 "./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
