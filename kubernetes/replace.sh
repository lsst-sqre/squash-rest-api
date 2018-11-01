#!/bin/bash

usage(){
	echo "Usage: $0 <template configuration> <configuration>"
	exit 1
}

if [ "$1" == "" ] || [ "$2" == "" ]; then
    usage
fi

# values returned if the service is not ready
HOST=""

# on GKE
WAIT_TIME=5
while [ "$HOST" == "" ] && [ "$WAIT_TIME" -le 20 ]; do
    echo "Waiting for the service to become available..."
    sleep $(( WAIT_TIME++ ))
    HOST=$(kubectl get service squash-restful-api -o jsonpath --template='{.status.loadBalancer.ingress[0].ip}')
done

if [ "$HOST" == "" ]; then
    echo "Service is not ready..."
    exit 1
fi

PORT=443
echo "Service address: $HOST:$PORT"

NAMESPACE=$(kubectl config current-context)

SQUASH_API_HOST="squash-restful-api-${NAMESPACE}.lsst.codes"

SQUASH_S3_BUCKET="squash-${NAMESPACE}.data"

if [ "$NAMESPACE" == "squash-prod" ]; then
    SQUASH_API_HOST="squash-restful-api.lsst.codes"
    SQUASH_S3_BUCKET="squash.data"
fi

if [ "$SQUASH_DEFAULT_USER" == "" ]; then
    echo "SQUASH_DEFAULT_USER not set."
    exit 1
fi

if [ "$SQUASH_DEFAULT_PASSWORD" == "" ]; then
    echo "SQUASH_DEFAULT_PASSWORD not set."
    exit 1
fi

if [ "$INSTANCE_CONNECTION_NAME" == "" ]; then
    echo "INSTANCE_CONNECTION_NAME not set."
    exit 1
fi

if [ "$INFLUXDB_API_URL" == "" ]; then
    echo "INFLUXDB_API_URL not set."
    exit 1
fi

if [ "$INFLUXDB_DATABASE" == "" ]; then
    echo "INFLUXDB_DATABASE not set."
    exit 1
fi

sed -e "
s/{{ TAG }}/${TAG}/
s/{{ SQUASH_API_HOST }}/${SQUASH_API_HOST}/
s/{{ SQUASH_S3_BUCKET }}/${SQUASH_S3_BUCKET}/
s/{{ SQUASH_DEFAULT_USER }}/${SQUASH_DEFAULT_USER}/
s/{{ SQUASH_DEFAULT_PASSWORD }}/${SQUASH_DEFAULT_PASSWORD}/
s/{{ SQUASH_ETL_MODE }}/\'${SQUASH_ETL_MODE}\'/
s/{{ INSTANCE_CONNECTION_NAME }}/${INSTANCE_CONNECTION_NAME}/
s|{{ INFLUXDB_API_URL }}|${INFLUXDB_API_URL}|
s/{{ INFLUXDB_DATABASE }}/${INFLUXDB_DATABASE}/

" $1 > $2
