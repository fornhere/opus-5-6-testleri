#!/bin/bash
# GPU işçisi: yalnız yeterli boş bellek varsa 30'ar karelik parçalar; diğer işlere yer bırakır
OUT="${1:?klasör gerekli}"; W=$2; SPP=$3; THR=$4; NEED=${5:-3400}; N=840
cd nefertiti-heykel/src
while true; do
  [ -e $OUT/DUR ] && exit 0
  [ $(ls $OUT | grep -c '^[0-9]*\.png$') -ge $N ] && exit 0
  FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)
  if [ "$FREE" -ge "$NEED" ]; then
    # yüksekten alçağa ilk boş 30 kare
    L=$(for f in $(seq $N -1 1); do p=$(printf "%s/%04d.png" $OUT $f); [ -e $p ] || [ -e $p.kilit ] || echo $f; done | head -30 | paste -sd,)
    [ -z "$L" ] && { sleep 30; continue; }
    blender -b ../film.blend -P render_film.py -- $OUT $W $SPP GPU $L $THR 2>&1 | grep --line-buffered -E "KARE|Error" | sed -u 's/^/GPU /'
  else sleep 45; fi
done
