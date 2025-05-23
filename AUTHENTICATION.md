# Campo Vision API Authentication Guide

This guide explains how to use the AWS Cognito authentication that has been added to the Campo Vision telemetry API.

## Overview

The Campo Vision API now uses AWS Cognito for authentication. All API endpoints are secured and require a valid JWT token to access. The authentication flow is as follows:

1. Users are created in the Cognito User Pool
2. Users authenticate and receive JWT tokens
3. JWT tokens are included in API requests as Bearer tokens
4. The API validates the tokens before processing requests

## Deployment

The authentication components are included in the SAM template and will be deployed automatically when you run:

```bash
sam build
sam deploy --guided
```

During the deployment, the following resources will be created:
- Cognito User Pool (CampoVisionUserPool)
- Cognito User Pool Client (CampoVisionUserPoolClient)
- API Gateway with Cognito Authorizer

## Creating Users

After deployment, you'll need to create users in the Cognito User Pool. You can do this using:

1. The AWS Management Console
2. The AWS CLI
3. The provided `test-auth.py` script

### Using the test-auth.py Script

The `test-auth.py` script can create users, authenticate, and test API endpoints:

```bash
# Create a new user
python test-auth.py --region us-east-1 \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --api-endpoint YOUR_API_ENDPOINT \
  --username user@example.com \
  --password YourPassword123! \
  --create-user

# Authenticate only
python test-auth.py --region us-east-1 \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --api-endpoint YOUR_API_ENDPOINT \
  --username user@example.com \
  --password YourPassword123!

# Send telemetry data
python test-auth.py --region us-east-1 \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --api-endpoint YOUR_API_ENDPOINT \
  --username user@example.com \
  --password YourPassword123! \
  --action ingest \
  --device-id my-device-001

# Retrieve telemetry data
python test-auth.py --region us-east-1 \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --api-endpoint YOUR_API_ENDPOINT \
  --username user@example.com \
  --password YourPassword123! \
  --action get \
  --device-id my-device-001
```

You can also set environment variables instead of passing command-line arguments:

```bash
export AWS_REGION=us-east-1
export USER_POOL_ID=YOUR_USER_POOL_ID
export USER_POOL_CLIENT_ID=YOUR_CLIENT_ID
export API_ENDPOINT=YOUR_API_ENDPOINT
export USERNAME=user@example.com
export PASSWORD=YourPassword123!

python test-auth.py --create-user
python test-auth.py --action ingest --device-id my-device-001
```

## Making Authenticated API Requests

To make authenticated requests to the API, you need to:

1. Obtain a JWT token from Cognito
2. Include the token in the Authorization header of your requests

### Example Using curl

```bash
# Authenticate and get token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=user@example.com,PASSWORD=YourPassword123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text)

# Send telemetry data
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/Prod/telemetry \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"device123","latitude":37.7749,"longitude":-122.4194,"temperature":25.5}'

# Get telemetry data
curl -X GET "https://your-api-id.execute-api.region.amazonaws.com/Prod/telemetry?deviceId=device123" \
  -H "Authorization: Bearer $TOKEN"
```

### Example Using Python

```python
import requests
import boto3

# Authenticate with Cognito
cognito_idp = boto3.client('cognito-idp', region_name='us-east-1')
response = cognito_idp.admin_initiate_auth(
    UserPoolId='YOUR_USER_POOL_ID',
    ClientId='YOUR_CLIENT_ID',
    AuthFlow='ADMIN_USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': 'user@example.com',
        'PASSWORD': 'YourPassword123!'
    }
)

# Extract token
token = response['AuthenticationResult']['AccessToken']

# Make authenticated request
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Send telemetry data
response = requests.post(
    'https://your-api-id.execute-api.region.amazonaws.com/Prod/telemetry',
    headers=headers,
    json={
        'deviceId': 'device123',
        'latitude': 37.7749,
        'longitude': -122.4194,
        'temperature': 25.5
    }
)

print(response.json())
```

## Token Validation

The API validates tokens by:
1. Verifying the token signature using the Cognito User Pool's public keys
2. Checking that the token is not expired
3. Validating that the token was issued for the correct client ID
4. Confirming that the token is an access token

If any of these checks fail, the API will return a 401 Unauthorized response.

## Common Issues

1. **Missing Authorization Header**: Ensure you're including the Authorization header with the Bearer token.
2. **Expired Token**: Tokens expire after a certain period. Re-authenticate to get a new token.
3. **Invalid Token Format**: The token should be prefixed with "Bearer " in the Authorization header.
4. **CORS Issues**: If you're calling the API from a browser, ensure your CORS configuration is correct.

## Security Considerations

- Never hardcode tokens in your application code
- Store tokens securely and refresh them when needed
- Use HTTPS for all API requests
- Implement token rotation and revocation strategies for production use
