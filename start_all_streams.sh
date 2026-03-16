#!/bin/bash

# This script starts all streams based on the configuration file

CONFIG_FILE="config.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Configuration file not found!"
    exit 1
fi

# Read each line of the configuration file and start the streams
while IFS= read -r line; do
    STREAM_COMMAND="${line}"
    echo "Starting stream: $STREAM_COMMAND"
    $STREAM_COMMAND
done < "$CONFIG_FILE"

echo "All streams have been started."