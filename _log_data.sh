#!/bin/bash
file=sd_volume/registry/registry.db

echo "- DRONE:"
sqlite3 $file "SELECT * FROM Drone"
echo "- TOKEN:"
sqlite3 $file "SELECT * FROM Token"
