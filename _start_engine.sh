#!/bin/bash
docker build\
    &> /dev/null\
    -t sd_engine\
    ./sd_engine
docker run\
    --network sd-drones_engine-network\
    --network-alias engine\
    sd_engine
