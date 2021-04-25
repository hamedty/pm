for i in 50 51 52 53 54 55
do
  echo 192.168.44.$i
  scp -rq /home/it/Desktop/PAM2060/firmware/.pio/build/due/firmware.bin  pi@192.168.44.$i:~/
  ssh pi@192.168.44.$i "./arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:sam:arduino_due_x --input-file firmware.bin"
  scp -rq /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/
done
