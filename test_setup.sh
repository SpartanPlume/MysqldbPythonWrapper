#!/usr/bin/bash

DB_TEST=$(jq -r '.DB_TEST' constants.json)
DB_USERNAME=$(jq -r '.DB_USERNAME' constants.json)
DB_PASSWORD=$(jq -r '.DB_PASSWORD' constants.json)

echo "Setting up mysql database... (Your mysql root user's password is needed)"
sudo mysql <<EOF
CREATE USER IF NOT EXISTS '$DB_USERNAME'@localhost IDENTIFIED BY '$DB_PASSWORD';
CREATE DATABASE IF NOT EXISTS $DB_TEST;
GRANT ALL PRIVILEGES ON $DB_TEST.* TO '$DB_USERNAME'@localhost;
FLUSH PRIVILEGES;
EOF
echo "Setting up mysql database... DONE"