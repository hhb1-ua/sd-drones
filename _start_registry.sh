#!/bin/bash
docker build\
    &> /dev/null\
    -t sd_registry\
    ./sd_registry
konsole\
    &> /dev/null\
    --hold\
    -e\
    docker run\
    --volume "$(pwd)/sd_volume/settings/":"/app/settings/"\
    --volume "$(pwd)/sd_volume/registry/":"/app/registry/"\
    --network sd-drones_engine-network\
    --network-alias registry\
    --publish "9010:9010"\
    sd_registry\
    &
