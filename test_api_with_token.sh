#!/bin/bash

# Check if token and API URL are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <access_token> <api_url>"
  echo "Example: $0 eyJraWQiOiJxYWx... https://your-api-id.execute-api.region.amazonaws.com/Prod"
  exit 1
fi

TOKEN=$1
API_URL=$2

echo "Testing API with token: ${TOKEN:0:10}..."

echo -e "\n1. Testing POST /telemetry endpoint (ingest telemetry data):"
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"tractor-auth-test","latitude":30.7749,"longitude":-100.4194,"temperature":25.5}' \
  $API_URL/telemetry

echo -e "\n\n2. Testing GET /telemetry endpoint (retrieve telemetry data):"
curl -X GET \
  -H "Authorization: Bearer $TOKEN" \
  "$API_URL/telemetry?deviceId=tractor-auth-test&startTime=2025-01-01T00:00:00Z&endTime=2025-12-31T23:59:59Z"

echo -e "\n"
