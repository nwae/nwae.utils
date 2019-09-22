#!/usr/bin/env bash

# Script name is the first parameter on command line
SCRIPT_NAME="$0"

#
# Required command line params
#   1. name: deployment name
#   2. cf: config file
#
# The program to startup
PROGRAM_NAME=""
# Deploy configuration, whether local, live, staging, vpo, welton, etc.
CF=""
RESTART_SCRIPT="restart.sh"
# Same for all live, staging or by vendor
DEPLOYMENT_FOLDER=$(pwd)

#
# Grab command line parameters
#
for keyvalue in "$@"; do
    echo "[$SCRIPT_NAME] Key value pair [$keyvalue]"
    IFS='=' # space is set as delimiter
    read -ra KV <<< "$keyvalue" # str is read into an array as tokens separated by IFS
    if [ "$KV" == "name" ] ; then
        PROGRAM_NAME="${KV[1]}"
        echo "[$SCRIPT_NAME] OK. Command line set param PROGRAM_NAME to $PROGRAM_NAME."
    elif [ "$KV" == "cf" ] ; then
        CF="${KV[1]}"
        echo "[$SCRIPT_NAME] OK. Command line set param CF to $CF."
    fi
done

echo "[$SCRIPT_NAME] Name '$PROGRAM_NAME' config '$CF' in '$DEPLOYMENT_FOLDER' restart script '$RESTART_SCRIPT'."
sleep 0.2

if [ "$PROGRAM_NAME" == "" ] || [ "$CF" == "" ]; then
  echo "[$SCRIPT_NAME] ERROR. Program name of config must not be empty!"
  exit 1
fi

#
# Sanity checks
#
echo "[$SCRIPT_NAME] Checking if we are in the right folder [$DEPLOYMENT_FOLDER].."
if [ "$(pwd)" != "$DEPLOYMENT_FOLDER" ]; then
  echo "[$SCRIPT_NAME] Script is not executing in the right folder $DEPLOYMENT_FOLDER. Instead in $(pwd)."
  exit 1
fi
echo "[$SCRIPT_NAME] OK. Folder check."
sleep 0.2

echo "[$SCRIPT_NAME] OK. Ready to deploy $PROGRAM_NAME."
sleep 0.2

# Check if restart script is present

#
# Now we are ready
#
if ! ls "$RESTART_SCRIPT" 1>/dev/null; then
  echo "[$SCRIPT_NAME] ERROR. Script [$RESTART_SCRIPT] not found!"
  exit 1
fi
echo "[$SCRIPT_NAME] OK. Restart script [$RESTART_SCRIPT] found. Calling script.."
sleep 0.2

#
# Main call into restart script
#
./$RESTART_SCRIPT name="$PROGRAM_NAME" cf="$CF"

if [ $? == 0 ]; then
  echo "[$SCRIPT_NAME] OK. $PROGRAM_NAME Deployment successful."
else
    echo "[$SCRIPT_NAME] ERROR. $PROGRAM_NAME Deployment exited with non-zero status."
fi
