#!/bin/bash

# Script name is the first parameter on command line
SCRIPT_NAME="$0"

########################################################################################
# Modify only these variables
########################################################################################
PROGRAM_NAME="YOUR PROGRAM NAME"
########################################################################################

PORT=

for keyvalue in "$@"; do
    echo "[$SCRIPT_NAME] Key value pair [$keyvalue]"
    IFS='=' # space is set as delimiter
    read -ra KV <<< "$keyvalue" # str is read into an array as tokens separated by IFS
    if [ "$KV" == "port" ] ; then
        PORT="${KV[1]}"
    fi
done

if [ "$PORT" == "" ] ; then
  echo "[$SCRIPT_NAME] ERROR No port specified to kill intent processes! Exit 1."
  exit 1
fi

echo "[$SCRIPT_NAME] $PROGRAM_NAME processes found at port $PORT.."
intent_processes=`lsof -ni :$PORT`
echo "$intent_processes"

while [ "$intent_processes" != '' ] ; do
    # Kill one by one, because for some cibai reason, doing the command kill -9 $(lsof -ti:$PORT)
    # won't work inside a script but works on command line
    IFS=', ' read -r -a PID_KILL <<< "$(lsof -ti :$PORT)"
    echo "[$SCRIPT_NAME] Killing $PROGRAM_NAME processes one by one. Killing PID ${PID_KILL[0]}.."
    kill -9 ${PID_KILL[0]}
    echo "[$SCRIPT_NAME] If can't kill please manually run the command: kill -9 \$(lsof -t -i:$PORT)"
    intent_processes=`lsof -ti :$PORT | sed s/"[^0-9]"//g`
    sleep 1
done
#for prc in $(lsof -t -i:"$PORT") ; do
#    echo "[$SCRIPT_NAME] Killing $prc..."
#    kill $prc
#done
