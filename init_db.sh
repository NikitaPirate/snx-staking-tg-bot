#!/bin/bash
chmod +x /docker-entrypoint-initdb.d/init_db.sh
echo "** Creating default DB and user for synthetix"

psql -c "
CREATE DATABASE synthetix;
"
psql -c "
CREATE USER synthetix_owner WITH ENCRYPTED PASSWORD '$SYNTHETIX_DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE synthetix TO synthetix_owner;
"
psql -d synthetix -c "
GRANT ALL ON SCHEMA public TO synthetix_owner;
"

echo "** Finished creating default DB and user for synthetix"
