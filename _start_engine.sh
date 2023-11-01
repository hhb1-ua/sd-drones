#!/bin/bash
clear
docker build -t sd_engine ./sd_engine
docker run --network sd-drones_engine-network --network-alias engine sd_engine
