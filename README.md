# Campo Vision

A comprehensive AWS-based telemetry system designed to track and monitor agricultural equipment in real-time. The platform provides fleet managers with live positioning data, historical analytics, and operational insights through an intuitive web interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Architecture Overview

Campo Vision is built on AWS using a serverless architecture with the following components:

- **API Gateway**: RESTful API endpoints for the web application
- **Lambda Functions**: Serverless compute for processing telemetry data
- **DynamoDB**: NoSQL database for storing equipment and telemetry data
- **S3**: Storage for processed data and web application hosting
- **CloudFront**: Content delivery network for the web application
- **Kinesis**: Real-time data streaming for telemetry data
- **IoT Core**: Manages device connections and message routing
- **EventBridge**: Scheduling and automation for maintenance alerts
- **SNS**: Notification service for alerts and updates

## Features

- Real-time equipment tracking and monitoring
- Historical data analysis and reporting
- Maintenance scheduling and alerts
- Mobile-responsive web interface
- Customizable dashboards and reports
- Equipment performance analytics
- Geofencing and boundary alerts

## Deployment

This project uses AWS SAM (Serverless Application Model) for infrastructure as code. To deploy:

```bash
# Install AWS SAM CLI if not already installed
# https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html

# Clone this repository
git clone https://github.com/yourusername/campo-vision.git
cd campo-vision

# Create a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install boto3

# Build the application
sam build

# Deploy the application
sam deploy --guided
```

During the guided deployment, you'll be asked to provide:
- Stack name (e.g., campo-vision)
- AWS Region
- Confirmation for IAM role creation

After deployment completes, you'll receive outputs including:
- API Gateway endpoint URL
- Lambda function ARNs
- DynamoDB table name

Save these outputs for future reference.

## Project Structure

```
/campo-vision
├── template.yaml         # AWS SAM template
├── functions/            # Lambda function code
│   ├── ingest-telemetry/
│   ├── get-telemetry/
│   ├── manage-equipment/
│   ├── process-telemetry/
│   ├── analytics/
│   └── maintenance/
├── web/                  # Web application frontend
└── README.md            # This file
```

## Development

### Prerequisites

- AWS Account
- AWS CLI configured with appropriate credentials
- AWS SAM CLI
- Python 3.9 or later

### API Access

Campo Vision provides open API endpoints for telemetry data ingestion and retrieval. The API is designed to be simple to use with standard HTTP methods.

### API Endpoints

The API provides the following endpoints:

- **POST /telemetry**: Ingest telemetry data from agricultural equipment
  - Accepts JSON with deviceId, latitude, longitude, and temperature
  - Returns confirmation with timestamp

- **GET /telemetry**: Retrieve telemetry data with filtering
  - Query parameters: deviceId (required), startTime, endTime, limit
  - Returns filtered telemetry data

### Local Testing

For local testing, you can use the provided scripts and Docker for DynamoDB local:

```bash
# Start local DynamoDB
docker-compose up -d

# Create the local DynamoDB table
python3 setup-local-dynamodb.py

# Test the Lambda functions locally
python3 test_ingest_locally.py
python3 test_get_locally.py

# Start API locally
sam local start-api

# Invoke a specific function with test events
sam local invoke IngestTelemetryFunction --event events/ingest-event.json
sam local invoke GetTelemetryFunction --event events/get-event.json
```

### Testing the API

After deploying to AWS, you can test the API using the provided script:

```bash
# Test the API endpoints
./direct_test.sh
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
