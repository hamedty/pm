for i in 100 101 102
do
  echo 192.168.44.$i
  ssh pi@192.168.44.$i "sudo shutdown -a now"
done
