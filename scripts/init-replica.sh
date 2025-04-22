#!/bin/bash

##################################
# For Development purposes only. #
##################################

echo ====================================================
echo ============= Initializing Replica Set =============
echo ====================================================

until mongosh --host mongo:27017 --eval 'quit(0)' &>/dev/null; do
    echo "Waiting for mongod to start..."
    sleep 5
done

echo "MongoDB started. Initiating Replica Set..."

mongosh --host mongo:27017 -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin <<EOF
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo:27017" }
  ]
})
EOF

echo ====================================================
echo ============= Replica Set initialized ==============
echo ====================================================