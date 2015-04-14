#!/usr/bin/env sh
cd $(dirname $(readlink -f $0))

# optionally supply settings here
python staalpiplayer.py
