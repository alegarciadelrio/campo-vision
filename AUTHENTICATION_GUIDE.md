# Campo Vision Authentication Guide

This guide explains how to use the Cognito authentication with your Campo Vision telemetry API.

## Authentication Flow

1. Users must be created in the Cognito User Pool
2. Users authenticate and receive a JWT token
3. API requests must include the JWT token in the Authorization header
4. The API validates the token and allows/denies access

## Creating Users

You can create users in several ways:

### Option 1: Using the AWS Console

1. Go to the AWS Cognito Console: https://console.aws.amazon.com/cognito/
2. Select your User Pool (you can find the ID in the CloudFormation outputs)
3. Click "Create user"
4. Fill in the required information (email, name, password)
5. Click "Create user"

### Option 2: Using the AWS CLI

```bash
aws cognito-idp admin-create-user \
  --user-pool-id YOUR_USER_POOL_ID \
  --username user@example.com \
  --user-attributes Name=email,Value=user@example.com Name=email_verified,Value=true Name=name,Value="User Name" \
  --temporary-password "TemporaryPassword123!" \
  --region YOUR_REGION
```

Then set a permanent password:

```bash
aws cognito-idp admin-set-user-password \
  --user-pool-id YOUR_USER_POOL_ID \
  --username user@example.com \
  --password "YourStrongPassword123!" \
  --permanent \
  --region YOUR_REGION
```

## Getting Authentication Tokens

### Option 1: Using the AWS CLI

```bash
aws cognito-idp admin-initiate-auth \
  --user-pool-id YOUR_USER_POOL_ID \
  --client-id YOUR_CLIENT_ID \
  --auth-flow ADMIN_USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=user@example.com,PASSWORD="YourStrongPassword123!" \
  --region YOUR_REGION
```

This will return an `AccessToken` that you can use to authenticate API requests.

### Option 2: Using the Hosted UI

You can use the Cognito Hosted UI to sign in and get tokens:

1. Go to the login URL provided in the CloudFormation outputs (CognitoLoginURL)
2. Sign in with your username and password
3. After successful authentication, you'll be redirected to a URL containing the access token in the fragment: `http://localhost:8080/#access_token=eyJra...&id_token=eyJ...&expires_in=3600&token_type=Bearer`
4. Extract the `access_token` value from the URL

## Testing the API with Authentication

Once you have an access token, you can use it to authenticate API requests:

### Using curl

```bash
# Test the ingest telemetry endpoint
curl -X POST \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"tractor-001","latitude":30.7749,"longitude":-100.4194,"temperature":25.5}' \
  YOUR_API_ENDPOINT/telemetry

# Test the get telemetry endpoint
curl -X GET \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  "YOUR_API_ENDPOINT/telemetry?deviceId=tractor-001&startTime=2025-01-01T00:00:00Z&endTime=2025-12-31T23:59:59Z"
```

### Using the test script

We've created a test script that you can use to test the API with an access token:

```bash
./test_api_with_token.sh YOUR_ACCESS_TOKEN
```

## Token Validation

The API validates tokens by:

1. Verifying the signature using the Cognito User Pool's public keys
2. Checking that the token is not expired
3. Verifying the issuer matches the Cognito User Pool
4. Extracting the user information from the token claims

If any of these checks fail, the API will return a 401 Unauthorized response.

## User Information

When a request is authenticated, the Lambda functions can access the user information from the token claims, including:

- User ID (sub)
- Email
- Username
- Group memberships (if any)

This information can be used for additional authorization checks or for auditing purposes.
