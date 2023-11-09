#!/bin/bash
start=0
number=1
network="sd-drones_engine-network"

while getopts s:n:l: flag
do
    case $flag in
        s) start=$OPTARG;;
        n) number=$OPTARG;;
        l) network=$OPTARG;;
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
        build\
        --rm\
        -t $container\
        --build-arg IDENTIFIER=$identifier\
        --build-arg ALIAS=$alias\
        ./sd_drone
    konsole\
        &> /dev/null\
        --hold\
        -e\
        docker run\
        --rm\
        --volume "$(pwd)/sd_volume/settings/":"/app/settings/"\
        --volume "$(pwd)/sd_volume/registry/":"/app/registry/"\
        --network $network\
        --network-alias $alias\
        $container\
        &
done
