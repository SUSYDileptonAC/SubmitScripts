#!/bin/bash

echo "Rearranging view"

screen -S $1 -X select 0

sleep 0.2
screen -S $1 -X split
sleep 0.2
screen -S $1 -X focus down
sleep 0.2
screen -S $1 -X select 1

sleep 0.2
screen -S $1 -X split
sleep 0.2
screen -S $1 -X focus down
sleep 0.2
screen -S $1 -X select 2

sleep 0.2
screen -S $1 -X split
sleep 0.2
screen -S $1 -X focus down
sleep 0.2
screen -S $1 -X select 3

sleep 0.2
screen -S $1 -X split
sleep 0.2
screen -S $1 -X focus down
sleep 0.2
screen -S $1 -X select 4
