#!/bin/bash
# kareler + ses -> cay-film.mp4
cd cay-kare/film
python3 - <<'P'
import glob
fs=sorted(glob.glob('kareler/s?_*.png')); print(len(fs))
open('liste.txt','w').write(''.join(f"file '{f}'\nduration 0.0416666667\n" for f in fs))
P
ffmpeg -v error -y -r 24 -pattern_type glob -i 'kareler/s?_*.png' -i ses.wav -map 0:v -map 1:a -vf "fade=t=in:st=0:d=0.45,fade=t=out:st=13.85:d=0.65,format=yuv420p" -af "highpass=f=40,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:v libx264 -preset slow -crf 15 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -t 14.5 -movflags +faststart ../cay-film.mp4
