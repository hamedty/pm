for i in 100
do
  echo 192.168.44.$i
  scp -rq /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/
  ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done
