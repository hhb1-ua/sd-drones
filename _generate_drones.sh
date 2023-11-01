#!/bin/bash
start=0
number=1
network="sd-drones_engine-network"
engine_adress="engine:9010"
broker_adress="kafka:9092"

while getopts s:n:l:e:b: flag
do
    case $flag in
        s) start=$OPTARG;;
        n) number=$OPTARG;;
        l) network=$OPTARG;;
        e) engine_adress=$OPTARG;;
        b) broker_adress=$OPTARG;;
    esac
done

for i in `seq $start $[$start + $number - 1]`
do
    # Argumentos del dron
    container="ct_autodrone_$i"
    identifier=$i
    alias="autodrone_$i"
    # Construir y ejecutar en una nueva ventana
    docker\
        &> /dev/null\
        build --rm -t $container\
        --build-arg DRONE_IDENTIFIER=$identifier\
        --build-arg DRONE_ALIAS=$alias\
        --build-arg ENGINE_ADRESS=$engine_adress\
        --build-arg BROKER_ADRESS=$broker_adress\
        ./sd_drone
    konsole\
        &> /dev/null\
        --hold\
        -e docker run --rm\
        --network $network\
        --network-alias alias\
        $container\
        &
done

# TODO: Eliminar el --hold al crear un nuevo terminal
