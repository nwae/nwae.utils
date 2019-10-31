#!/usr/bin/env bash

# Script name is the first parameter on command line
SCRIPT_NAME="$0"

#
# Command line parameters
#
#PORT=5001
#CONFIGFILE=0
#GUNICORN_WORKERS=4
#WORKER_TYPE="sync"
#WORKER_TYPE_FLAG=""
#INTENT_ENGINES="http://localhost:5000/"

for keyvalue in "$@"; do
    echo "[$SCRIPT_NAME] Key value pair [$keyvalue]"
    IFS='=' # space is set as delimiter
    read -ra KV <<< "$keyvalue" # str is read into an array as tokens separated by IFS
    if [ "$KV" == "workers" ] ; then
        GUNICORN_WORKERS="${KV[1]}"
        echo "[$SCRIPT_NAME]  Set number of gunicorn workers to $GUNICORN_WORKERS."
    elif [ "$KV" == "workertype" ] ; then
        WORKER_TYPE="${KV[1]}"
        if [ "$WORKER_TYPE" == "gthread" ] ; then
            echo "[$SCRIPT_NAME]  Worker type is gthread, setting 2 threads."
            WORKER_TYPE_FLAG="--thread=2"
        fi
        echo "[$SCRIPT_NAME]  Set worker type to $WORKER_TYPE."
    elif [ "$KV" == "port" ] ; then
        PORT="${KV[1]}"
        echo "[$SCRIPT_NAME] Set port to $PORT."
    elif [ "$KV" == "configfile" ] ; then
        CONFIGFILE="${KV[1]}"
        echo "[$SCRIPT_NAME] Set configfile to $CONFIGFILE."
    fi
done
