#!/bin/bash
docker build\
    -t sd_weather\
    ./sd_weather
docker run\
    --network sd-drones_engine-network\
    --network-alias weather\
    sd_weather
