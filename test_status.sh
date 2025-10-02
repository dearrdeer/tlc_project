#!/bin/bash

# Script to test the /status endpoint

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
API_URL="http://localhost:8000/status"

# Check if task ID is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <task_id>"
    echo "Please provide a task ID as an argument"
    exit 1
fi

TASK_ID="$1"

# Send GET request
echo "Checking status for task ID: $TASK_ID"

response=$(curl -s -w "%{http_code}" -X GET "$API_URL?task_id=$TASK_ID")

http_code="${response: -3}"
response_body="${response%???}"

# Check response
if [ "$http_code" -eq 200 ]; then
    echo "Success! Response:"
    echo "$response_body" | jq .
elif [ "$http_code" -eq 404 ]; then
    echo "Task not found: $http_code"
    echo "$response_body" | jq .
else
    echo "Error: HTTP $http_code"
    echo "$response_body" | jq .
fi