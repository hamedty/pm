for i in 100 #103 106 108 109 110
do
  echo 192.168.44.$i
  scp -rq /home/it/Desktop/PAM2060/firmware/.pio/build/due/firmware.bin  pi@192.168.44.$i:~/
  ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
  ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
  ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM2 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"

  # scp -rq /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/
  # ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done
