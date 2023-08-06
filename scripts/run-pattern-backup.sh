#!/bin/bash

cd /home/volumio/volco

dt=$(date +"%Y-%m-%d")
cp static/playlist_patterns.json "backup/playlist-patterns-$dt.json"
