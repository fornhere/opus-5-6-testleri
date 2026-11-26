#!/bin/bash
# ara kopya (1440p, kayıpsıza yakın) + ses -> son film; derece: bloom, vinyet, gren
cd nefertiti-heykel
ffmpeg -y -loglevel error -i "$1" -i test/ses.wav -filter_complex "[0:v]format=gbrp10le,split[v1][v2];\
[v2]curves=all='0/0 0.55/0 0.8/0.45 1/1',scale=640:360:flags=area,gblur=sigma=9,scale=2560:1440:flags=bicubic,format=gbrp10le[bl];\
[v1][bl]blend=all_mode=screen:all_opacity=0.40,vignette=angle=PI/8:dither=1,noise=alls=4:allf=t,fade=t=out:st=27.0:d=0.95,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[o]" \
 -map "[o]" -map 1:a -c:v libx264 -preset slow -crf 17 -profile:v high -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a aac -b:a 256k -movflags +faststart -t 28 "$2"
