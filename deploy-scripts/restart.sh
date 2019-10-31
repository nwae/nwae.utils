#!/bin/bash

# Script name is the first parameter on command line
SCRIPT_NAME="$0"
PROGRAM_NAME="SAMPLE PROGRAM"

# SERVER_SCRIPT_DIR="server.scripts"
SOURCE_DIR="src"

# Default config is nothing
CF=""

################################################################################
# Config Files
################################################################################
CONFIGFILE_LOCAL="../app.data/config/local.cf"
CONFIGFILE_STAGING="../app.data/config/staging.cf"
CONFIGFILE_LIVE="../app.data/config/live.cf"
# Default to live
CONFIGFILE="$CONFIGFILE_LIVE"

#
# Test Commands
#
TEST_CMD_LOCAL="http://localhost:port/?..."
TEST_CMD_LIVE="http://..."
TEST_CMD_STAGING="http://..."
# Default to live
TEST_CMD="$TEST_CMD"

PORT=

for keyvalue in "$@"; do
    echo "[$SCRIPT_NAME] Key value pair [$keyvalue]"
    IFS='=' # space is set as delimiter
    read -ra KV <<< "$keyvalue" # str is read into an array as tokens separated by IFS
    if [ "$KV" == "cf" ] ; then
        CF="${KV[1]}"
        if [ "$CF" == "local" ] ; then
            CONFIGFILE="$CONFIGFILE_LOCAL"
            PORT=7000
            TEST_CMD="$TEST_CMD_LOCAL"
        elif [ "$CF" == "live" ] ; then
            CONFIGFILE="$CONFIGFILE_LIVE"
            PORT=7000
            TEST_CMD="$TEST_CMD_LIVE"
        elif [ "$CF" == "staging" ] ; then
            CONFIGFILE="$CONFIGFILE_STAGING"
            PORT=7000
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
if ! ./kill.sh port="$PORT"; then
  echo "[$SCRIPT_NAME] ERROR $PROGRAM_NAME Unable to kill existing processes.."
  exit 1
fi

#
# STDOUT & STDERR FILES PATH
#
STDOUTERRFILE="../app.data/server/$CF.$PORT.outerr."`date +%Y-%m-%d_%H%M%S`".log"
echo ""
echo ""
echo "[$SCRIPT_NAME] ***** RESTARTING $PROGRAM_NAME $CF PORT $PORT *****"
# Need to go to source folder
echo "[$SCRIPT_NAME] Going into folder ../$SOURCE_DIR"
cd "../$SOURCE_DIR" || echo "[$SCRIPT_NAME] ERROR Failed to go into source dir!"
echo "[$SCRIPT_NAME] Executing in folder $(pwd), configfile=$CONFIGFILE port=$PORT with out/err files $STDOUTERRFILE"
if ! ./run.gunicorn.sh \
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
# Ask user to review STDOUT log
#
echo "[$SCRIPT_NAME] ********************* USER STDOUT / STDERR REVIEW ($PROGRAM_NAME STARTUP) *********************"
tail -30 "$STDOUTFILE"
echo "[$SCRIPT_NAME] Please review tail results (last 30 lines) from startup for stdout log ($STDOUTERRFILE) above."
read -p "[$SCRIPT_NAME] Ok to proceed? (yes/no): " ok_to_proceed
if [ "$ok_to_proceed" != "yes" ]; then
  echo "[$SCRIPT_NAME] ERROR. User refuse to proceed after viewing stdout log. Exiting.."
  exit 1
fi

#
# Test server via curl
#
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

# Go back to where we came from
cd - || echo "[$SCRIPT_NAME] ERROR Failed to go back to original folder."

