#!/bin/sh
# Try ISP mainpath nodes for a usable format
for node in 11 12 13 14 15; do
    echo "--- Testing /dev/video$node ---"
    v4l2-ctl -d /dev/video$node --list-formats-ext 2>&1 | head -8
done
