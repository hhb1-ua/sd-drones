#!/bin/bash
start=1
number=1

while getopts s:n:l: flag
do
    case $flag in
        s) start=$OPTARG;;
        n) number=$OPTARG;;
    esac
done

for i in `seq $start $[$start + $number - 1]`
do
    # Argumentos del dron
    identifier=$i
    alias="autodrone_$i"
    password="user"

    # Construir y ejecutar en una nueva ventana
    bash\
        _start_drone.sh\
        $identifier\
        $alias\
        $password
done
