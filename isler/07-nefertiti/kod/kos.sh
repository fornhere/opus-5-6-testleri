#!/bin/bash
cd nefertiti-heykel/src
r() { blender -b ../$1 -P render_film.py -- ../kareler 1280 $2 CPU $3 .08 2>&1 | grep --line-buffered -E "KARE|Error"; }
r film.blend 8 182-252
r film.blend 9 253-432
r film_b.blend 8 433-471
r film_b.blend 9 472-558
r film_b.blend 9 583-756
echo BITTI
