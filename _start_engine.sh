#!/bin/bash
reload=0

while getopts r arg
do
    case $arg in
        r) reload=1;;
    esac
done

docker build\
    &> /dev/null\
    -t sd_engine\
    --build-arg RELOAD=$reload\
    ./sd_engine
docker run\
    --interactive\
    --tty\
    --volume "$(pwd)/sd_volume/settings/":"/app/settings/"\
    --volume "$(pwd)/sd_volume/registry/":"/app/registry/"\
    --volume "$(pwd)/sd_volume/engine/":"/app/engine/"\
    --volume "$(pwd)/sd_volume/certificate/":"/app/certificate/"\
    --network sd-drones_engine-network\
    --network-alias engine\
    --publish "9020:9020"\
    --publish "9030:9030"\
    sd_engine
