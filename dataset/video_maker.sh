for f in *192*
do
  echo $f
  ffmpeg -n -r 50 -loglevel error -i $f/%03d_00.png -c:v libx264 -vf fps=25 -pix_fmt yuv420p $f/video.mp4
done
