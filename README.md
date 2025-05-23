# Campo Vision

A comprehensive AWS-based telemetry system designed to track and monitor agricultural equipment in real-time. The platform provides fleet managers with live positioning data, historical analytics, and operational insights through an intuitive web interface.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Architecture Overview

Campo Vision is built on AWS using a serverless architecture with the following components:

- **API Gateway**: RESTful API endpoints with Cognito authentication
- **Lambda Functions**: Serverless compute for processing telemetry data
- **DynamoDB**: NoSQL database for storing telemetry data with device ID and timestamp keys
- **Cognito**: User authentication and authorization
- **SAM (Serverless Application Model)**: Infrastructure as code for deployment

## Features

- **Secure API Endpoints**: All endpoints protected with Cognito authentication
- **Real-time Telemetry Ingestion**: Store device location and sensor data
- **Flexible Data Retrieval**: Query telemetry data by device ID and time ranges
- **Token-based Authentication**: Support for both ID tokens and access tokens

## API Endpoints

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/telemetry` | POST | Ingest telemetry data | Cognito JWT |
| `/telemetry` | GET | Retrieve telemetry data with filtering | Cognito JWT |

## Getting Started

### Prerequisites

- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- Python 3.12 or higher
- An AWS account with access to Cognito, API Gateway, Lambda, and DynamoDB

### Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/campo-vision.git
cd campo-vision
```

2. Deploy the application using SAM

```bash
sam build
sam deploy --guided
```

3. Note the outputs from the deployment, including:
   - API Gateway endpoint URL
   - Cognito User Pool ID
   - Cognito User Pool Client ID

### Authentication Setup

1. Create a user in the Cognito User Pool

```bash
aws cognito-idp admin-create-user \
  --user-pool-id YOUR_USER_POOL_ID \
  --username user@example.com \
  --user-attributes Name=email,Value=user@example.com Name=email_verified,Value=true Name=name,Value="Test User" \
  --temporary-password "Temporary123!" \
  --region YOUR_REGION
```

2. Set a permanent password for the user

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id YOUR_USER_POOL_ID \
  --username user@example.com \
  --password "YourPassword123!" \
  --permanent \
  --region YOUR_REGION
```

3. Obtain authentication tokens

```bash
aws cognito-idp admin-initiate-auth \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=user@example.com,PASSWORD="YourPassword123!" \
  --region YOUR_REGION
```

### Testing the API

Use the included test script to authenticate and make API requests:

```bash
python test-auth.py \
  --region YOUR_REGION \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --api-endpoint YOUR_API_ENDPOINT \
  --username user@example.com \
  --password YourPassword123! \
  --action get \
  --device-id YOUR_DEVICE_ID
```

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
