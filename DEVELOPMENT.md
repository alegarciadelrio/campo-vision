# Campo Vision Development Guide

This document contains helpful commands and tips for developing the Campo Vision telemetry system.

## Local Testing

### Running DynamoDB Locally

```bash
# Start local DynamoDB (requires Docker)
docker-compose up -d

# Create the local DynamoDB table
aws dynamodb create-table \
    --table-name TelemetryTable \
    --attribute-definitions \
        AttributeName=deviceId,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=deviceId,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000
```

### Testing Lambda Functions Locally

```bash
# Test ingest telemetry function
sam local invoke IngestTelemetryFunction --event events/ingest-event.json

# Test get telemetry function
sam local invoke GetTelemetryFunction --event events/get-event.json

# Start API locally
sam local start-api
```

## API Testing Commands

### Ingest Telemetry Data

```bash
# Replace API_ENDPOINT with your actual API endpoint
curl -X POST ${API_ENDPOINT}/telemetry \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"tractor-001","latitude":30.7749,"longitude":-100.4194,"temperature":26.5}'
```

### Retrieve Telemetry Data

```bash
# Replace API_ENDPOINT with your actual API endpoint
curl "${API_ENDPOINT}/telemetry?deviceId=tractor-001&startTime=2025-01-01T00:00:00Z&endTime=2025-12-31T23:59:59Z"
```

## Deployment

```bash
# Build the application
sam build

# Deploy the application
sam deploy --guided
```

## Useful AWS CLI Commands

```bash
# List DynamoDB tables
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Scan DynamoDB table (local)
aws dynamodb scan --table-name TelemetryTable --endpoint-url http://localhost:8000

# Scan DynamoDB table (AWS)
aws dynamodb scan --table-name TelemetryTable
```
