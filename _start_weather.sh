#!/bin/bash
cp settings.json sd_weather/

docker build\
    &> /dev/null\
    -t sd_weather\
    ./sd_weather
konsole\
    &> /dev/null\
    --hold\
    -e\
    docker run\
    --network sd-drones_engine-network\
    --network-alias weather\
    sd_weather\
    &
