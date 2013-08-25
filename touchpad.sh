#! /bin/bash

# File: touchpad.sh
# Enable touchpad and set with customize settings.

if egrep -iq 'touchpad' /proc/bus/input/devices; then
   synclient VertEdgeScroll=1 &
   synclient TapButton1=1 &
   synclient ClickPad=1
   synclient TapButton2=2
   synclient RightButtonAreaLeft=1630
   synclient RightButtonAreaRight=3300
   synclient RightButtonAreaTop=1500
   synclient RightButtonAreaBottom=1800
fi

echo "OK"
