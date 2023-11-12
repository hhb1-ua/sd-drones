#!/bin/bash
echo "DELETE FROM Registry WHERE 1 = 1;" | sqlite3 sd_volume/registry/registry.db
