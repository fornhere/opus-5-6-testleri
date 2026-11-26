#!/bin/bash
cd esik-film
for S in s1 s4 s3 s2 s5; do ./run.sh full src/shots.py -- shot=$S spp=128 >> test/full.log 2>&1
 [ $S = s1 ] && ./run.sh full src/shots.py -- shot=s1 spp=128 noring=1 out=$PWD/frames/s1b >> test/full.log 2>&1; done; echo ALLDONE >> test/full.log
