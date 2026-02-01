#!/usr/bin/env bash

API_KEY="550e8400-e29b-41d4-a716-446655440000"
BASE_URL="http://localhost:8000"

# Create a task
echo "Creating task..."
response=$(curl -s -X POST "${BASE_URL}/task?x=5&y=3" \
  -H "Authorization: Bearer ${API_KEY}")

task_id=$(echo "$response" | jq -r '.task_id')
echo "Task created: $task_id"

# Poll until SUCCESS
echo "Polling for result..."
while true; do
  poll_response=$(curl -s -X GET "${BASE_URL}/poll/${task_id}")
  state=$(echo "$poll_response" | jq -r '.state')

  if [ "$state" = "SUCCESS" ]; then
    result=$(echo "$poll_response" | jq -r '.result')
    echo "Task completed! Result: $result"
    break
  fi

  echo "State: $state - waiting..."
  sleep 1
done
