#!/usr/bin/env bash

SRC="Flash_Firmware/"
FileName=$(echo $1 | rev | cut -d '/' -f1 | rev)

cd ~/$SRC;
echo "We are in dir::\$PWD"
gcc -O ./src/program_fpga_Nex.c  -l bcm2835 -o ./bin/NexFlash.exe
sudo ./bin/NexFlash.exe < HEX_Files/$FileName
sleep 1;