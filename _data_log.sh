#!/bin/bash
registry=sd_volume/registry/registry.db
auditory=sd_volume/engine/auditory.db

echo "- DRONE:"
sqlite3 $registry "SELECT * FROM Drone"
echo "- TOKEN:"
sqlite3 $registry "SELECT * FROM Token"
echo "- AUDIT:"
sqlite3 $auditory "SELECT * FROM Auditory"
