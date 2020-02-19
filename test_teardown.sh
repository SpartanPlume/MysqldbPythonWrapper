#!/usr/bin/bash

DB_TEST=$(jq -r '.DB_TEST' constants.json)
DB_USERNAME=$(jq -r '.DB_USERNAME' constants.json)
DB_PASSWORD=$(jq -r '.DB_PASSWORD' constants.json)

echo "Tearing down mysql database... (Your mysql root user's password is needed)"
sudo mysql <<EOF
DROP USER IF EXISTS '$DB_USERNAME'@localhost;
DROP DATABASE IF EXISTS $DB_TEST;
FLUSH PRIVILEGES;
EOF
echo "Tearing down mysql database... DONE"