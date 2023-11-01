#!/bin/bash
start=0
number=1

while getopts s:n: flag
do
    case $flag in
        s) start=$OPTARG;;
        n) number=$OPTARG;;
    esac
done

for i in `seq $start $[$number - 1]`
do
    echo $i
done
