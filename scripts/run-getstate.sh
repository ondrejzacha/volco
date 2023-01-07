#!/bin/bash

state=$(curl -s localhost:3000/api/v1/getState)
ts=$(date +"%Y-%m-%d %H:%M:%S")
record="{\"ts\": \"$ts\", \"state\": $state}"

if [[ $state =~ '"status":"play"' ]]; then
    echo $record >> /home/volumio/volco/logs/state.log
fi
