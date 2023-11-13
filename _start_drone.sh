#!/bin/bash
identifier=$1
alias=$2
token=$3
network="sd-drones_engine-network"

# while getopts t: flag
# do
#     case $flag in
#         t) token=$OPTARG;;
#     esac
# done

echo $token

docker\
    &> /dev/null\
    build\
    --rm\
    -t $alias\
    --build-arg IDENTIFIER=$identifier\
    --build-arg ALIAS=$alias\
    --build-arg TOKEN=$token\
    ./sd_drone
konsole\
    &> /dev/null\
    --hold\
    -e\
    docker run\
    --rm\
    --volume "$(pwd)/sd_volume/settings/":"/app/settings/"\
    --network $network\
    --network-alias $alias\
    $alias\
    &

