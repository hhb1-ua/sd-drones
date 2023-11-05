#!/bin/bash
docker build\
    -t sd_registry\
    ./sd_registry
konsole\
    &> /dev/null\
    --hold\
    -e\
    docker run\
    --network sd-drones_engine-network\
    --network-alias registry\
    sd_registry\
    &
