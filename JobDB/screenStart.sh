#!/bin/bash

echo "Setting up screens"
echo "Creating 4 windows"

screen -S $1 -X stuff $'top\r'
./screenCreate.sh $1
./screenCreate.sh $1
./screenCreate.sh $1
./screenCreate.sh $1
