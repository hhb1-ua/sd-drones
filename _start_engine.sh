#!/bin/bash
docker build\
    &> /dev/null\
    -t sd_engine\
    ./sd_engine
konsole\
    &> /dev/null\
    --hold\
    -e\
    docker run\
    --volume "$(pwd)/sd_volume/settings/":"/app/settings/"\
    --volume "$(pwd)/sd_volume/registry/":"/app/registry/"\
    --volume "$(pwd)/sd_volume/engine/":"/app/engine/"\
    --network sd-drones_engine-network\
    --network-alias engine\
    sd_engine\
    &
