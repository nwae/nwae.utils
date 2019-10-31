#!/bin/bash

# Script name is the first parameter on command line
SCRIPT_NAME="$0"

########################################################################################
# Modify only these variables
########################################################################################
# Where this script is relative to project directory
PROGRAM_NAME="YOUR PROGRAM NAME"
LOGFILE_FOLDER=".."
DO_TEST_AFTER_START=0
# Config Files
CONFIGFILE_LOCAL="../app.data/config/local.cf"
CONFIGFILE_LIVE="../app.data/config/live.cf"
CONFIGFILE_STAGING="../app.data/config/staging.cf"
# Default Ports
PORT_LOCAL=7000
PORT_LIVE=7000
PORT_STAGING=7000
# Test Commands
TEST_CMD_LOCAL="http://localhost:port/?..."
TEST_CMD_LIVE="http://..."
TEST_CMD_STAGING="http://..."
################################################################################

# Default config is nothing
CF=
CONFIGFILE=
PORT=
TEST_CMD=

for keyvalue in "$@"; do
    echo "[$SCRIPT_NAME] Key value pair [$keyvalue]"
    IFS='=' # space is set as delimiter
    read -ra KV <<< "$keyvalue" # str is read into an array as tokens separated by IFS
    if [ "$KV" == "cf" ] ; then
        CF="${KV[1]}"
        if [ "$CF" == "local" ] ; then
            CONFIGFILE="$CONFIGFILE_LOCAL"
            PORT="$PORT_LOCAL"
            TEST_CMD="$TEST_CMD_LOCAL"
        elif [ "$CF" == "live" ] ; then
            CONFIGFILE="$CONFIGFILE_LIVE"
            PORT="$PORT_LIVE"
            TEST_CMD="$TEST_CMD_LIVE"
        elif [ "$CF" == "staging" ] ; then
            CONFIGFILE="$CONFIGFILE_STAGING"
            PORT="$PORT_STAGING"
            TEST_CMD="$TEST_CMD_STAGING"
        else
          echo "[$SCRIPT_NAME] ERROR Invalid cf=$CF. Exiting script.."
          exit 1
        fi
    fi
done

if [ "$CF" == "" ]; then
  echo "[$SCRIPT_NAME] ERROR $PROGRAM_NAME Must specify config cf=[live, local, staging, ...]"
  exit 1
fi

echo "[$SCRIPT_NAME] $PROGRAM_NAME For config $CF, set configfile to $CONFIGFILE, port to $PORT."

#
# Kill Intent APIs wrapped in gunicorn
#
echo "[$SCRIPT_NAME] Try to kill $PROGRAM_NAME processes.."
if ! ./kill.by.port.sh port="$PORT"; then
  echo "[$SCRIPT_NAME] ERROR $PROGRAM_NAME Unable to kill existing processes.."
  exit 1
else
  echo "[$SCRIPT_NAME] OK Successfully killed $PROGRAM_NAME processes."
fi

#
# STDOUT & STDERR FILES PATH
#
STDOUTERRFILE="$LOGFILE_FOLDER/$CF.$PORT.outerr."`date +%Y-%m-%d_%H%M%S`".log"
echo ""
echo ""
echo "[$SCRIPT_NAME] ***** RESTARTING $PROGRAM_NAME $CF PORT $PORT *****"
echo "[$SCRIPT_NAME] Executing in folder $(pwd), configfile=$CONFIGFILE port=$PORT with out/err files '$STDOUTERRFILE'."
if ! ./run.python.sh \
        configfile="$CONFIGFILE" \
        port="$PORT" \
        >"$STDOUTERRFILE" 2>&1 &
then
  echo "[$SCRIPT_NAME] ERROR Failed to run $PROGRAM_NAME."
fi
disown

#
# Sleep a little, then check stderr log for user to verify
#
echo "[$SCRIPT_NAME] Waiting for 5 secs to capture output from $PROGRAM_NAME startup.."
sleep 5
#
# Ask user to review STDOUT / STDERR log
#
echo "[$SCRIPT_NAME] ********************* USER STDOUT / STDERR REVIEW ($PROGRAM_NAME STARTUP) *********************"
tail -30 "$STDOUTERRFILE"
echo "[$SCRIPT_NAME] Please review tail results (last 30 lines) from startup for stdout log ($STDOUTERRFILE) above."
read -p "[$SCRIPT_NAME] Ok to proceed? (yes/no): " ok_to_proceed
if [ "$ok_to_proceed" != "yes" ]; then
  echo "[$SCRIPT_NAME] ERROR. User refuse to proceed after viewing stdout log. Exiting.."
  exit 1
fi

#
# Test server via curl
#
if [ $DO_TEST_AFTER_START -eq 1 ]; then
  echo "[$SCRIPT_NAME] Doing tests on $PROGRAM_NAME via curl..."
  echo "[$SCRIPT_NAME] Executing command curl -X GET $TEST_CMD"
  curl -X GET "$TEST_CMD"
  echo ""
  echo "[$SCRIPT_NAME] ********************* USER AUTOMATIC TEST REVIEW ($PROGRAM_NAME STARTUP) *********************"
  read -p "[$SCRIPT_NAME] Ok to proceed from above test result? (yes/no): " ok_to_proceed
  if [ "$ok_to_proceed" != "yes" ]; then
    echo "[$SCRIPT_NAME] ERROR. User refuse to proceed after viewing return value from automatic tests. Exiting.."
    exit 1
  fi
fi