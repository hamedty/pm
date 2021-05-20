for i in  101 #102 #100 101 102
do
  echo 192.168.44.$i
  scp -rq /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/
  # scp -rq /home/it/Desktop/PAM2060/models/holder_$i.clf pi@192.168.44.$i:~/
  # ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done
