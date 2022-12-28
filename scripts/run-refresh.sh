#!/bin/bash

cd /home/volumio/volco
source venv/bin/activate

date >> logs/refresh.log
refresh | tee -a logs/refresh.log
