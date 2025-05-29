#!/usr/bin/env python3
"""
Campo Vision - Telemetry Data Generator

This script sends simulated telemetry data to the Campo Vision API every minute.
It authenticates with AWS Cognito and sends data for a specified device.

Usage:
    python send_telemetry.py

Environment variables:
    AWS_REGION - AWS region (default: us-east-1)
    USER_POOL_ID - Cognito User Pool ID
    USER_POOL_CLIENT_ID - Cognito User Pool Client ID
    API_ENDPOINT - API Gateway endpoint URL
    USERNAME - Cognito username (email)
    PASSWORD - Cognito password
    DEVICE_ID - Device ID for telemetry data (default: test-device-001)
"""

import os
import json
import boto3
import requests
import time
import random
import logging
import argparse
import dotenv
from datetime import datetime

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading .env file from: {env_path}")
# Force reload to override any existing environment variables
dotenv.load_dotenv(env_path, override=True)

# Print loaded environment variables for debugging
print(f"Loaded environment variables:")
print(f"USER_POOL_ID: {os.environ.get('USER_POOL_ID')}")
print(f"USER_POOL_CLIENT_ID: {os.environ.get('USER_POOL_CLIENT_ID')}")
print(f"API_ENDPOINT: {os.environ.get('API_ENDPOINT')}")
print(f"USERNAME: {os.environ.get('USERNAME')}")
print(f"DEVICE_ID: {os.environ.get('DEVICE_ID')}")
# Don't print password for security reasons

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Send telemetry data to Campo Vision API')
parser.add_argument('--region', help='AWS Region', default=os.environ.get('AWS_REGION', 'us-east-1'))
parser.add_argument('--user-pool-id', help='Cognito User Pool ID', default=os.environ.get('USER_POOL_ID'))
parser.add_argument('--client-id', help='Cognito User Pool Client ID', default=os.environ.get('USER_POOL_CLIENT_ID'))
parser.add_argument('--api-endpoint', help='API Gateway Endpoint URL', default=os.environ.get('API_ENDPOINT'))
parser.add_argument('--username', help='Cognito Username (email)', default=os.environ.get('USERNAME'))
parser.add_argument('--password', help='Cognito Password', default=os.environ.get('PASSWORD'))
parser.add_argument('--device-id', help='Device ID for telemetry data', default=os.environ.get('DEVICE_ID', 'test-device-001'))
parser.add_argument('--interval', type=int, help='Interval in seconds between data points', default=5)
parser.add_argument('--lat', type=float, help='Base latitude', default=-34.0915)
parser.add_argument('--lon', type=float, help='Base longitude', default=-56.2455)

args = parser.parse_args()

# Validate required arguments
required_args = ['user_pool_id', 'client_id', 'api_endpoint', 'username', 'password']
missing_args = [arg for arg in required_args if not getattr(args, arg)]
if missing_args:
    logger.error(f"Missing required arguments: {', '.join(missing_args)}")
    logger.error("Please provide them as command line arguments or environment variables.")
    exit(1)

# Initialize Cognito Identity Provider client
cognito_idp = boto3.client('cognito-idp', region_name=args.region)

class TokenManager:
    """Manages authentication tokens and refreshes them when needed"""
    
    def __init__(self, user_pool_id, client_id, username, password):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.username = username
        self.password = password
        self.tokens = None
        self.token_expiry = 0
        
    def get_valid_token(self):
        """Get a valid token, refreshing if necessary"""
        current_time = time.time()
        
        # If we have no tokens or they're about to expire (within 5 minutes)
        if not self.tokens or current_time > (self.token_expiry - 300):
            self.authenticate()
            
        return self.tokens['id_token']
        
    def authenticate(self):
        """Authenticate with Cognito and get tokens"""
        try:
            # Log authentication attempt details (without password)
            logger.info(f"Attempting to authenticate with Cognito:")
            logger.info(f"  User Pool ID: {self.user_pool_id}")
            logger.info(f"  Client ID: {self.client_id}")
            logger.info(f"  Username: {self.username}")
            
            # Initiate auth
            response = cognito_idp.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='ADMIN_USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': self.username,
                    'PASSWORD': self.password
                }
            )
            
            # Extract tokens
            self.tokens = {
                'id_token': response['AuthenticationResult']['IdToken'],
                'access_token': response['AuthenticationResult']['AccessToken'],
                'refresh_token': response['AuthenticationResult']['RefreshToken'],
                'expires_in': response['AuthenticationResult']['ExpiresIn']
            }
            
            # Calculate expiry time
            self.token_expiry = time.time() + self.tokens['expires_in']
            
            logger.info("Authentication successful!")
            logger.info(f"Token expires in: {self.tokens['expires_in']} seconds")
            
            return True
        except boto3.exceptions.botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            logger.error(f"Cognito authentication error: {error_code} - {error_message}")
            
            if error_code == 'NotAuthorizedException':
                logger.error("Please check your username and password")
            elif error_code == 'UserNotFoundException':
                logger.error("User does not exist in the User Pool")
            elif error_code == 'InvalidParameterException':
                logger.error("Check that your User Pool ID and Client ID are correct")
            
            return False
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def generate_telemetry_data(device_id, base_lat, base_lon):
    """Generate random telemetry data"""
    # Add more significant variations to position
    # This will create movement in an area of approximately 1-2 km radius
    lat_variation = random.uniform(-0.01, 0.01)  # About 1-2 km in latitude
    lon_variation = random.uniform(-0.01, 0.01)  # About 1-2 km in longitude
    
    # Add some drift to simulate movement patterns
    global last_lat_drift, last_lon_drift
    if not hasattr(generate_telemetry_data, 'last_lat_drift'):
        generate_telemetry_data.last_lat_drift = 0
        generate_telemetry_data.last_lon_drift = 0
    
    # Create some continuity in movement (80% influenced by previous direction)
    drift_factor = 0.8
    new_lat_drift = random.uniform(-0.002, 0.002)
    new_lon_drift = random.uniform(-0.002, 0.002)
    
    generate_telemetry_data.last_lat_drift = (drift_factor * generate_telemetry_data.last_lat_drift + 
                                             (1 - drift_factor) * new_lat_drift)
    generate_telemetry_data.last_lon_drift = (drift_factor * generate_telemetry_data.last_lon_drift + 
                                             (1 - drift_factor) * new_lon_drift)
    
    # Generate random temperature between 15 and 35 degrees
    temperature = random.uniform(15.0, 35.0)
    
    # Generate random speed between 0 and 30 km/h
    speed = random.uniform(0.0, 30.0)
    
    return {
        'deviceId': device_id,
        'latitude': base_lat + lat_variation + generate_telemetry_data.last_lat_drift,
        'longitude': base_lon + lon_variation + generate_telemetry_data.last_lon_drift,
        'temperature': round(temperature, 2),
        'speed': round(speed, 2),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

def send_telemetry(token_manager, api_endpoint, telemetry_data):
    """Send telemetry data to the API"""
    try:
        # Get a valid token
        token = token_manager.get_valid_token()
        
        # Send request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        endpoint = api_endpoint.rstrip('/') + '/telemetry'
        response = requests.post(endpoint, json=telemetry_data, headers=headers)
        
        # Check response
        if response.status_code == 201:
            logger.info("Telemetry data sent successfully!")
            return True
        else:
            logger.error(f"Error sending telemetry data: {response.status_code}")
            logger.error(json.dumps(response.json(), indent=2))
            return False
    except Exception as e:
        logger.error(f"Error sending telemetry data: {str(e)}")
        return False

def main():
    """Main function"""
    logger.info(f"Starting telemetry data generator for device: {args.device_id}")
    logger.info(f"Data will be sent every {args.interval} seconds")
    
    # Initialize token manager
    token_manager = TokenManager(
        args.user_pool_id,
        args.client_id,
        args.username,
        args.password
    )
    
    # Initial authentication
    if not token_manager.authenticate():
        logger.error("Failed to authenticate. Exiting.")
        return
    
    try:
        # Main loop
        while True:
            # Generate telemetry data
            telemetry_data = generate_telemetry_data(args.device_id, args.lat, args.lon)
            logger.info(f"Generated telemetry data: {telemetry_data}")
            
            # Send data
            success = send_telemetry(token_manager, args.api_endpoint, telemetry_data)
            if success:
                logger.info(f"Successfully sent data for device {args.device_id}")
            else:
                logger.warning(f"Failed to send data for device {args.device_id}")
            
            # Wait for the next interval
            logger.info(f"Waiting {args.interval} seconds until next data point...")
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        logger.info("Script interrupted by user. Exiting.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()
