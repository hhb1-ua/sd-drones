#!/bin/bash
docker build\
    &> /dev/null\
    -t sd_registry\
    ./sd_registry
docker run\
    --interactive\
    --tty\
    --volume "$(pwd)/sd_volume/settings/":"/app/settings/"\
    --volume "$(pwd)/sd_volume/registry/":"/app/registry/"\
    --volume "$(pwd)/sd_volume/certificate/":"/app/certificate/"\
    --network sd-drones_engine-network\
    --network-alias registry\
    --publish "9010:9010"\
    sd_registry
