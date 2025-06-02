#!/usr/bin/env python3
"""
Certificate Management Script for Campo Vision

This script generates X.509 certificates for ESP32 devices and registers them with AWS IoT Core.
It can be used by your backend API to provision new devices through the Android app.

Usage:
  python create_device_certificate.py --device-id <device-id> [--company-id <company-id>] [--skip-dynamodb]
  python create_device_certificate.py --device-id dev-massey-ferguson-178 --company-id comp-a786e492-4883-4ade-b948-a818c2465fd8
"""

import argparse
import boto3
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

def create_certificate(device_id, company_id=None):
    """
    Creates an X.509 certificate for a device and registers it with AWS IoT Core
    
    Args:
        device_id (str): Unique identifier for the device
        company_id (str, optional): Company ID to associate with the device
        
    Returns:
        dict: Certificate information including certificateArn, certificateId, 
              certificatePem, privateKey, and thing name
    """
    # Initialize AWS IoT client
    iot_client = boto3.client('iot')
    
    # Prefix for thing name
    prefix = os.environ.get('THING_NAME_PREFIX', 'campo-vision-')
    thing_name = f"{prefix}{device_id}"
    
    # Check if thing already exists
    try:
        iot_client.describe_thing(thingName=thing_name)
        print(f"Thing {thing_name} already exists")
        thing_exists = True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            thing_exists = False
        else:
            raise e
    
    # Create certificate
    certificate_response = iot_client.create_keys_and_certificate(setAsActive=True)
    
    certificate_arn = certificate_response['certificateArn']
    certificate_id = certificate_response['certificateId']
    certificate_pem = certificate_response['certificatePem']
    private_key = certificate_response['keyPair']['PrivateKey']
    
    # Get policy name from environment or use default
    policy_name = os.environ.get('IOT_POLICY_NAME', 'CampoVisionIoTPolicy')
    
    # Attach policy to certificate
    try:
        iot_client.attach_policy(
            policyName=policy_name,
            target=certificate_arn
        )
    except ClientError as e:
        # Clean up certificate if policy attachment fails
        iot_client.update_certificate(
            certificateId=certificate_id,
            newStatus='INACTIVE'
        )
        iot_client.delete_certificate(
            certificateId=certificate_id,
            forceDelete=True
        )
        raise Exception(f"Error attaching policy: {str(e)}")
    
    # Create or update thing
    try:
        if not thing_exists:
            # Create thing
            thing_response = iot_client.create_thing(
                thingName=thing_name,
                attributePayload={
                    'attributes': {
                        'deviceId': device_id,
                        'companyId': company_id if company_id else 'unassigned'
                    }
                }
            )
        else:
            # Update thing attributes
            thing_response = iot_client.update_thing(
                thingName=thing_name,
                attributePayload={
                    'attributes': {
                        'deviceId': device_id,
                        'companyId': company_id if company_id else 'unassigned'
                    },
                    'merge': True
                }
            )
    except ClientError as e:
        # Clean up certificate if thing creation fails
        iot_client.update_certificate(
            certificateId=certificate_id,
            newStatus='INACTIVE'
        )
        iot_client.delete_certificate(
            certificateId=certificate_id,
            forceDelete=True
        )
        print(f"Error creating thing: {str(e)}")
        raise e
    
    # Attach certificate to thing
    try:
        iot_client.attach_thing_principal(
            thingName=thing_name,
            principal=certificate_arn
        )
    except ClientError as e:
        # Clean up if attaching fails
        if not thing_exists:
            iot_client.delete_thing(thingName=thing_name)
        iot_client.update_certificate(
            certificateId=certificate_id,
            newStatus='INACTIVE'
        )
        iot_client.delete_certificate(
            certificateId=certificate_id,
            forceDelete=True
        )
        raise Exception(f"Error attaching certificate to thing: {str(e)}")
    
    # Add thing to the Campo Vision Thing Group
    try:
        # Get group name from environment or use default
        group_name = os.environ.get('IOT_THING_GROUP', 'CampoVisionDevices')
        
        # Add thing to group
        iot_client.add_thing_to_thing_group(
            thingName=thing_name,
            thingGroupName=group_name
        )
        print(f"Added device {thing_name} to group {group_name}")
    except ClientError as e:
        print(f"Warning: Could not add device to thing group: {str(e)}")
        # We don't raise an exception here as this is not critical for device creation
    
    # Save certificates to files
    save_certificate_files(device_id, certificate_pem, private_key)
    
    # Return device information
    device_info = {
        'deviceId': device_id,
        'thingName': thing_name,
        'certificateArn': certificate_arn,
        'certificateId': certificate_id
    }
    
    if company_id:
        device_info['companyId'] = company_id
    
    print(f"Successfully created certificate and thing for device {device_id}")
    print(f"Certificate files saved to certificates/{device_id}/")
    
    return device_info

def save_certificate_files(device_id, certificate_pem, private_key):
    output_dir = f"certificates/{device_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f"{output_dir}/certificate.pem", "w") as cert_file:
        cert_file.write(certificate_pem)
        
    with open(f"{output_dir}/private.key", "w") as key_file:
        key_file.write(private_key)
        
    # Get AWS IoT endpoint
    iot_client = boto3.client('iot')
    endpoint_response = iot_client.describe_endpoint(endpointType='iot:Data-ATS')
    endpoint = endpoint_response['endpointAddress']
    
    with open(f"{output_dir}/config.json", "w") as config_file:
        config = {
            "deviceId": device_id,
            "endpoint": endpoint
        }
        json.dump(config, config_file, indent=2)

def register_device_in_dynamodb(device_info):
    """
    Registers the device in the DynamoDB device table
    
    Args:
        device_info (dict): Device information including deviceId and companyId
    """
    try:
        # Initialize DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        
        # Get table name from environment or use default
        table_name = os.environ.get('DEVICE_TABLE', 'DeviceTable')
        print(f"Using DynamoDB table: {table_name}")
        
        table = dynamodb.Table(table_name)
        
        # Create item for DynamoDB
        device_item = {
            'deviceId': device_info['deviceId'],
            'thingName': device_info['thingName'],
            'certificateId': device_info['certificateId'],
            'createdAt': datetime.utcnow().isoformat(),
            'status': 'ACTIVE'
        }
        
        # Add company ID if provided
        if device_info.get('companyId'):
            device_item['companyId'] = device_info['companyId']
        
        # Store in DynamoDB
        table.put_item(Item=device_item)
        
        print(f"Device {device_info['deviceId']} registered in DynamoDB")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Error: DynamoDB table '{table_name}' not found.")
            print("Make sure you have deployed the SAM template and set the correct DEVICE_TABLE environment variable.")
            print("The certificate was still created successfully.")
        else:
            print(f"Error registering device in DynamoDB: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error registering device in DynamoDB: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create IoT certificate for ESP32 device')
    parser.add_argument('--device-id', required=True, help='Device ID')
    parser.add_argument('--company-id', help='Company ID')
    parser.add_argument('--skip-dynamodb', action='store_true', help='Skip registering in DynamoDB')
    
    args = parser.parse_args()
    
    try:
        # Create certificate and thing
        device_info = create_certificate(args.device_id, args.company_id)
        
        # Register device in DynamoDB (unless skipped)
        if not args.skip_dynamodb:
            register_device_in_dynamodb(device_info)
        
        # Print success message
        print(f"Device {args.device_id} successfully provisioned")
        print(f"Certificate files are in certificates/{args.device_id}/")
        
    except Exception as e:
        print(f"Error provisioning device: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
