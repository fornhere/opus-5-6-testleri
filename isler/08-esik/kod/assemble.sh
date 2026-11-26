#!/bin/bash
cd esik-film
for w in 0 1 2; do systemd-run --user --wait --collect --unit=esik-g$w -p MemoryMax=1200M -p MemorySwapMax=0 -p Nice=10 -p WorkingDirectory=$PWD blender -b --factory-startup -P src/grade.py -- w=$w n=3 & done; wait
N=$(ls out/png | wc -l); echo "png $N"
FONT=$(fc-match -f '%{file}' 'Noto Serif:style=Light')
ffmpeg -v error -y -framerate 24 -i out/png/%05d.png -i audio/score.wav -vf "drawtext=fontfile='$FONT':text='E  Ş  İ  K':fontcolor=white:fontsize=58:x=(w-tw)/2:y=h*0.80:alpha='if(lt(t,44.2),0,if(lt(t,45.6),(t-44.2)/1.4,if(lt(t,46.7),1,max(0,1-(t-46.7)/1.1))))'" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p -c:a aac -b:a 320k -shortest -movflags +faststart out/ESIK.mp4
ffprobe -v error -show_entries stream=codec_name,width,height,nb_frames,duration -of csv out/ESIK.mp4
