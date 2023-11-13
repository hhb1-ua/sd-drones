#!/bin/bash
echo "DELETE FROM Registry WHERE 1 = 1;" | sqlite3 sd_volume/registry/registry.db
sqlite3 &> /dev/null sd_volume/registry/registry.db < sd_volume/registry/create.sql
echo "Data has been wiped"
