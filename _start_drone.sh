#!/bin/bash
identifier=$1
alias=$2
password=$3

# while getopts t: flag
# do
#     case $flag in
#         t) token=$OPTARG;;
#     esac
# done

docker\
    &> /dev/null\
    build\
    --rm\
    -t $alias\
    --build-arg IDENTIFIER=$identifier\
    --build-arg ALIAS=$alias\
    --build-arg PASSWORD=$password\
    ./sd_drone
konsole\
    &> /dev/null\
    --hold\
    -e\
    docker run\
    --rm\
    --volume "$(pwd)/sd_volume/settings/":"/app/settings/"\
    --volume "$(pwd)/sd_volume/certificate/":"/app/certificate/"\
    --network sd-drones_engine-network\
    --network-alias $alias\
    --publish-all\
    $alias\
    &

