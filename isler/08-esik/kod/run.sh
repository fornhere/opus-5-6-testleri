#!/bin/bash
# Blender in its own cgroup with a hard memory ceiling, so it can never take the desktop down
name=$1; shift
systemctl --user reset-failed esik-$name 2>/dev/null
exec systemd-run --user --wait --pipe --collect --unit=esik-$name -p MemoryMax=5G -p MemorySwapMax=0 -p CPUWeight=30 -p Nice=10 -p WorkingDirectory=esik-film blender -b --factory-startup -P "$@"
