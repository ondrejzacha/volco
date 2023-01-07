#!/bin/bash

cd /home/volumio/volco
source venv/bin/activate

echo -e '\n' >> logs/refresh.log
date >> logs/refresh.log
refresh | tee -a logs/refresh.log
