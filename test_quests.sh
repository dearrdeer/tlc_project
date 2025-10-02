#!/bin/bash

# Script to test the /new endpoint with questsH.json data

# Check if required tools are available
if ! command -v curl &> /dev/null; then
    echo "Error: curl is not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed"
    exit 1
fi

# API endpoint
API_URL="http://localhost:8000/new"

# JSON data file
DATA_FILE="./sample_dataset/questsH.json"

# Check if data file exists
if [ ! -f "$DATA_FILE" ]; then
    echo "Error: Data file $DATA_FILE not found"
    exit 1
fi

# Send POST request
echo "Sending quests data to $API_URL"

response=$(curl -s -w "%{http_code}" -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "@$DATA_FILE")

http_code="${response: -3}"
response_body="${response%???}"

# Check response
if [ "$http_code" -eq 200 ]; then
    echo "Success! Response:"
    echo "$response_body" | jq .
    task_id=$(echo "$response_body" | jq -r '.taskid')
    echo "Task ID: $task_id"
else
    echo "Error: HTTP $http_code"
    echo "$response_body" | jq .
fi