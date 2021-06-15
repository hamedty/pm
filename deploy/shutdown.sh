for i in 100 101 #102 103 104 105 106 107 108 109 110
do
  echo 192.168.44.$i
  ssh pi@192.168.44.$i "sudo shutdown -a now" &
done
