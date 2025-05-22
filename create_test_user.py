import boto3
import json
import os
import sys
import argparse
import getpass
from botocore.exceptions import ClientError

def create_user(cognito_idp_client, user_pool_id, email, password, name):
    """Create a user in the Cognito User Pool"""
    try:
        # Create the user
        response = cognito_idp_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'name',
                    'Value': name
                }
            ],
            MessageAction='SUPPRESS'  # Don't send an email
        )
        
        # Set the user's password
        cognito_idp_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        print(f"User {email} created successfully")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            print(f"User {email} already exists")
            return True
        else:
            print(f"Error creating user: {str(e)}")
            return False

def authenticate_user(cognito_idp_client, user_pool_id, client_id, email, password):
    """Authenticate a user and get tokens"""
    try:
        # Authenticate the user
        response = cognito_idp_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        # Extract tokens
        auth_result = response.get('AuthenticationResult', {})
        access_token = auth_result.get('AccessToken')
        id_token = auth_result.get('IdToken')
        refresh_token = auth_result.get('RefreshToken')
        
        if not access_token:
            print("Authentication failed: No access token returned")
            return None
        
        print("Authentication successful")
        return {
            'AccessToken': access_token,
            'IdToken': id_token,
            'RefreshToken': refresh_token
        }
    
    except ClientError as e:
        print(f"Authentication error: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Create a test user in Cognito User Pool')
    parser.add_argument('--user-pool-id', required=True, help='Cognito User Pool ID')
    parser.add_argument('--client-id', required=True, help='Cognito User Pool Client ID')
    parser.add_argument('--email', required=True, help='User email')
    parser.add_argument('--name', default='Test User', help='User name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    # Get password from user input (don't show in console)
    password = getpass.getpass('Enter password (min 8 chars, uppercase, lowercase, number): ')
    
    # Create Cognito IDP client
    cognito_idp_client = boto3.client('cognito-idp', region_name=args.region)
    
    # Create the user
    if create_user(cognito_idp_client, args.user_pool_id, args.email, password, args.name):
        # Authenticate the user
        tokens = authenticate_user(cognito_idp_client, args.user_pool_id, args.client_id, args.email, password)
        
        if tokens:
            # Save tokens to a file
            with open('auth_tokens.json', 'w') as f:
                json.dump(tokens, f, indent=2)
            
            print("\nTokens saved to auth_tokens.json")
            print("\nTo use the access token for API requests:")
            print(f"curl -H \"Authorization: Bearer {tokens['AccessToken']}\" https://your-api-endpoint.com/path")
            
            # Create a sample curl command for the API
            with open('test_api.sh', 'w') as f:
                f.write(f"""#!/bin/bash
# Test the ingest telemetry endpoint
curl -X POST \\
  -H "Authorization: Bearer {tokens['AccessToken']}" \\
  -H "Content-Type: application/json" \\
  -d '{{"deviceId":"tractor-test","latitude":30.7749,"longitude":-100.4194,"temperature":25.5}}' \\
  https://bret2220d3.execute-api.us-east-1.amazonaws.com/Prod/telemetry

echo ""
echo "---------------------------------------"
echo ""

# Test the get telemetry endpoint
curl -X GET \\
  -H "Authorization: Bearer {tokens['AccessToken']}" \\
  "https://bret2220d3.execute-api.us-east-1.amazonaws.com/Prod/telemetry?deviceId=tractor-test&startTime=2025-01-01T00:00:00Z&endTime=2025-12-31T23:59:59Z"
""")
            
            os.chmod('test_api.sh', 0o755)
            print("\nTest script created: test_api.sh")

if __name__ == '__main__':
    main()
