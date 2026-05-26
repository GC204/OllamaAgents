#!/bin/bash
# PostgreSQL initialization script for remote access

# Wait for PostgreSQL to start
sleep 5

# Update pg_hba.conf to allow remote connections
echo "host    all             all             0.0.0.0/0               md5" >> /var/lib/postgresql/data/pg_hba.conf

# Reload PostgreSQL configuration
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT pg_reload_conf();" || true

echo "PostgreSQL configuration updated for remote access"
