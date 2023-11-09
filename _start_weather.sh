#!/bin/bash
docker build\
    &> /dev/null\
    -t sd_weather\
    ./sd_weather
konsole\
    &> /dev/null\
    --hold\
    -e\
    docker run\
    --volume "$(pwd)/sd_volume/settings/":"/app/settings/"\
    --volume "$(pwd)/sd_volume/weather/":"/app/weather/"\
    --network sd-drones_engine-network\
    --network-alias weather\
    sd_weather\
    &
