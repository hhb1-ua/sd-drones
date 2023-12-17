#!/bin/bash
registry=sd_volume/registry/registry.db
auditory=sd_volume/engine/auditory.db

if test -f "$registry"; then
    echo "Wiping registry data..."
    echo "DELETE FROM Drone WHERE 1 = 1;" | sqlite3 $registry
    echo "DELETE FROM Token WHERE 1 = 1;" | sqlite3 $registry
else
    echo "Setting up registry database..."
    sqlite3 $registry < sd_volume/registry/create.sql
fi

if test -f "$auditory"; then
    echo "Wiping auditory data..."
    echo "DELETE FROM Token WHERE 1 = 1;" | sqlite3 $auditory
    echo "DELETE FROM Drone WHERE 1 = 1;" | sqlite3 $auditory
else
    echo "Setting up auditory database..."
    sqlite3 $auditory < sd_volume/engine/create.sql
fi

echo "Operation successful"


