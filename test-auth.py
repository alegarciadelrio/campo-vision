#!/usr/bin/env python3
"""
Campo Vision - Cognito Authentication Test Script

This script demonstrates how to authenticate with AWS Cognito and make authenticated
requests to the Campo Vision API.

Usage:
    python test-auth.py

Environment variables:
    AWS_REGION - AWS region (default: us-east-1)
    USER_POOL_ID - Cognito User Pool ID
    USER_POOL_CLIENT_ID - Cognito User Pool Client ID
    API_ENDPOINT - API Gateway endpoint URL
    USERNAME - Cognito username (email)
    PASSWORD - Cognito password
"""

import os
import json
import boto3
import requests
import argparse
from datetime import datetime

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test Cognito Authentication for Campo Vision API')
parser.add_argument('--region', help='AWS Region', default=os.environ.get('AWS_REGION', 'us-east-1'))
parser.add_argument('--user-pool-id', help='Cognito User Pool ID', default=os.environ.get('USER_POOL_ID'))
parser.add_argument('--client-id', help='Cognito User Pool Client ID', default=os.environ.get('USER_POOL_CLIENT_ID'))
parser.add_argument('--api-endpoint', help='API Gateway Endpoint URL', default=os.environ.get('API_ENDPOINT'))
parser.add_argument('--username', help='Cognito Username (email)', default=os.environ.get('USERNAME'))
parser.add_argument('--password', help='Cognito Password', default=os.environ.get('PASSWORD'))
parser.add_argument('--create-user', action='store_true', help='Create a new user if it does not exist')
parser.add_argument('--device-id', help='Device ID for telemetry data', default='test-device-001')
parser.add_argument('--action', choices=['auth', 'ingest', 'get'], default='auth', 
                    help='Action to perform: auth (authenticate only), ingest (send telemetry), get (retrieve telemetry)')

args = parser.parse_args()

# Validate required arguments
required_args = ['user_pool_id', 'client_id', 'api_endpoint', 'username', 'password']
missing_args = [arg for arg in required_args if not getattr(args, arg)]
if missing_args:
    print(f"Error: Missing required arguments: {', '.join(missing_args)}")
    print("Please provide them as command line arguments or environment variables.")
    exit(1)

# Initialize Cognito Identity Provider client
cognito_idp = boto3.client('cognito-idp', region_name=args.region)

def create_user_if_not_exists():
    """Create a new user in Cognito if it doesn't exist"""
    try:
        # Check if user exists
        cognito_idp.admin_get_user(
            UserPoolId=args.user_pool_id,
            Username=args.username
        )
        print(f"User {args.username} already exists")
        return True
    except cognito_idp.exceptions.UserNotFoundException:
        if args.create_user:
            try:
                # Create new user
                cognito_idp.admin_create_user(
                    UserPoolId=args.user_pool_id,
                    Username=args.username,
                    TemporaryPassword=args.password,
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': args.username
                        },
                        {
                            'Name': 'email_verified',
                            'Value': 'true'
                        },
                        {
                            'Name': 'name',
                            'Value': 'Test User'
                        }
                    ]
                )
                
                # Set permanent password
                cognito_idp.admin_set_user_password(
                    UserPoolId=args.user_pool_id,
                    Username=args.username,
                    Password=args.password,
                    Permanent=True
                )
                
                print(f"Created new user: {args.username}")
                return True
            except Exception as e:
                print(f"Error creating user: {str(e)}")
                return False
        else:
            print(f"User {args.username} does not exist. Use --create-user to create it.")
            return False
    except Exception as e:
        print(f"Error checking user: {str(e)}")
        return False

def authenticate():
    """Authenticate with Cognito and get tokens"""
    try:
        # Initiate auth
        response = cognito_idp.admin_initiate_auth(
            UserPoolId=args.user_pool_id,
            ClientId=args.client_id,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': args.username,
                'PASSWORD': args.password
            }
        )
        
        # Extract tokens
        tokens = {
            'id_token': response['AuthenticationResult']['IdToken'],
            'access_token': response['AuthenticationResult']['AccessToken'],
            'refresh_token': response['AuthenticationResult']['RefreshToken'],
            'expires_in': response['AuthenticationResult']['ExpiresIn']
        }
        
        print("Authentication successful!")
        print(f"Access Token: {tokens['access_token'][:20]}...{tokens['access_token'][-10:]}")
        print(f"Token expires in: {tokens['expires_in']} seconds")
        
        return tokens
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None

def ingest_telemetry(access_token):
    """Send telemetry data to the API"""
    try:
        # Prepare telemetry data
        telemetry_data = {
            'deviceId': args.device_id,
            'latitude': 37.7749,
            'longitude': -122.4194,
            'temperature': 25.5,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Send request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        endpoint = args.api_endpoint.rstrip('/') + '/telemetry'
        response = requests.post(endpoint, json=telemetry_data, headers=headers)
        
        # Check response
        if response.status_code == 201:
            print("Telemetry data sent successfully!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"Error sending telemetry data: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
            return False
    except Exception as e:
        print(f"Error sending telemetry data: {str(e)}")
        return False

def get_telemetry(access_token):
    """Retrieve telemetry data from the API"""
    try:
        # Prepare request
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        endpoint = args.api_endpoint.rstrip('/') + f'/telemetry?deviceId={args.device_id}'
        response = requests.get(endpoint, headers=headers)
        
        # Check response
        if response.status_code == 200:
            print("Telemetry data retrieved successfully!")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"Error retrieving telemetry data: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
            return False
    except Exception as e:
        print(f"Error retrieving telemetry data: {str(e)}")
        return False

def main():
    """Main function"""
    # Create user if requested
    if args.create_user and not create_user_if_not_exists():
        return
    
    # Authenticate
    tokens = authenticate()
    if not tokens:
        return
    
    # Perform requested action
    if args.action == 'ingest':
        ingest_telemetry(tokens['id_token'])  # Use ID token instead of access token
    elif args.action == 'get':
        get_telemetry(tokens['id_token'])  # Use ID token instead of access token
    
    print("\nDone!")

if __name__ == '__main__':
    main()
