for i in  101 102 103 104 105 #100 101 # 102
do
  echo 192.168.44.$i
  scp -rq /home/it/Desktop/PAM2060/server/ pi@192.168.44.$i:~/
  # scp -r /home/it/Desktop/PAM2060/models/holder_$i.clf pi@192.168.44.$i:~/models/holder.clf
  # scp -r /home/it/Desktop/PAM2060/models/dosing_$i.clf pi@192.168.44.$i:~/models/dosing.clf
  ssh pi@192.168.44.$i "sudo systemctl restart rpi.service"
done
