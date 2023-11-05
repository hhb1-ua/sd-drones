#!/bin/bash
topic="test-topic"
message="HelloWorld!"
number=1
partition=0
network="sd-drones_engine-network"

while getopts t:m:n:p: flag
do
    case $flag in
        t) topic=$OPTARG;;
        m) message=$OPTARG;;
        n) number=$OPTARG;;
        p) partition=$OPTARG;;
    esac
done

docker\
    &> /dev/null\
    build\
    --rm\
    -t producer\
    --build-arg TOPIC=$topic\
    --build-arg MESSAGE=$message\
    --build-arg NUMBER=$number\
    --build-arg PARTITION=$partition\
    ./sd_testing/producer

docker run\
    --rm\
    --network $network\
    --network-alias producer\
    producer
