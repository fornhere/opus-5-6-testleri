#!/bin/bash
# kareler -> nefertiti_film.mp4
cd nefertiti-heykel
miss=$(for f in $(seq 1 558) $(seq 583 756); do [ -e $(printf kareler/%04d.png $f) ] || echo -n "$f "; done)
[ -n "$miss" ] && { echo "EKSIK: $miss"; [ "$1" != "zorla" ] && exit 1; }
UP="scale=1920:1080:flags=lanczos+accurate_rnd,unsharp=5:5:0.45:5:5:0,setsar=1,format=gbrp"
ffmpeg -y -loglevel error -stats \
 -framerate 30 -start_number 1   -i kareler/%04d.png \
 -framerate 30 -start_number 182 -i kareler/%04d.png \
 -framerate 30 -start_number 583 -i kareler/%04d.png \
 -f lavfi -i color=black:s=1920x1080:r=30:d=0.8 -i test/ses.wav \
 -filter_complex "[0:v]trim=end_frame=181,setpts=PTS-STARTPTS,scale=1920:1080,setsar=1,format=gbrp[a];\
[1:v]trim=end_frame=377,setpts=PTS-STARTPTS,$UP[b];[3:v]format=gbrp,setsar=1,trim=end_frame=24,setpts=PTS-STARTPTS[k];\
[2:v]trim=end_frame=174,setpts=PTS-STARTPTS,$UP[c];[a][b][k][c]concat=n=4:v=1:a=0[v];\
[v]split[v1][v2];[v2]curves=all='0/0 0.55/0 0.8/0.45 1/1',scale=480:270:flags=area,gblur=sigma=7,scale=1920:1080:flags=bicubic[bl];\
[v1][bl]blend=all_mode=screen:all_opacity=0.42,vignette=angle=PI/5.5,noise=alls=4:allf=t,fade=t=out:st=24.25:d=0.9,format=yuv420p[o]" \
 -map "[o]" -map 4:a -c:v libx264 -preset medium -crf 15 -profile:v high -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a aac -b:a 256k -movflags +faststart -t 25.2 ${2:-nefertiti_film.mp4}
