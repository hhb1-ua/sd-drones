#!/bin/bash
topic="test-topic"
partition=0
network="sd-drones_engine-network"

while getopts t:p: flag
do
    case $flag in
        t) topic=$OPTARG;;
        p) partition=$OPTARG;;
    esac
done

docker\
    &> /dev/null\
    build\
    --rm\
    -t consumer\
    --build-arg TOPIC=$topic\
    --build-arg PARTITION=$partition\
    ./sd_testing/consumer

docker run\
    --rm\
    --network $network\
    --network-alias consumer\
    consumer
