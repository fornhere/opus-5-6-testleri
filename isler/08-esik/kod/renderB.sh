#!/bin/bash
cd esik-film
while systemctl --user is-active -q esik-driver; do sleep 5; done
./run.sh full src/end.py -- shot=s8 spp=128 >> test/full.log 2>&1
./run.sh full src/end.py -- shot=s7 spp=160 >> test/full.log 2>&1
./run.sh full src/gal2.py -- spp=64 >> test/full.log 2>&1
echo ALLDONE_B >> test/full.log
