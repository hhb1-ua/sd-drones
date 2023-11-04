#!/bin/bash
docker build\
    -t sd_engine\
    ./sd_engine
konsole\
    &> /dev/null\
    --hold\
    docker run\
    --network sd-drones_engine-network\
    --network-alias engine\
    sd_engine\
    &
