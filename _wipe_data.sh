#!/bin/bash
file=sd_volume/registry/registry.db

if test -f "$file"; then
    echo "Wiping data..."
    echo "DELETE FROM Drone WHERE 1 = 1;" | sqlite3 $file
    echo "DELETE FROM Token WHERE 1 = 1;" | sqlite3 $file
else
    echo "Setting up database..."
    sqlite3 $file < sd_volume/registry/create.sql
    # &> /dev/null
fi

echo "Operation successful"


