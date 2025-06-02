#!/usr/bin/env python3
"""
Device Group Management Script for Campo Vision

This script manages AWS IoT Thing Groups for Campo Vision devices.
It can add devices to groups, remove devices from groups, and list devices in groups.

Usage:
  python manage_device_groups.py --add-device <device-id> [--group-name <group-name>]
  python manage_device_groups.py --remove-device <device-id> [--group-name <group-name>]
  python manage_device_groups.py --list-devices [--group-name <group-name>]
  python manage_device_groups.py --list-groups
  python manage_device_groups.py --add-all-devices [--group-name <group-name>]
"""

import argparse
import boto3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

def add_device_to_group(device_id, group_name=None):
    """
    Adds a device to an IoT Thing Group
    
    Args:
        device_id (str): Device ID or Thing Name of the device
        group_name (str, optional): Name of the Thing Group. Defaults to CampoVisionDevices.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Initialize AWS IoT client
    iot_client = boto3.client('iot')
    
    # Default group name
    if not group_name:
        group_name = os.environ.get('IOT_THING_GROUP', 'CampoVisionDevices')
    
    # Prefix for thing name
    prefix = os.environ.get('THING_NAME_PREFIX', 'campo-vision-')
    
    # If device_id doesn't start with the prefix, add it
    if not device_id.startswith(prefix):
        thing_name = f"{prefix}{device_id}"
    else:
        thing_name = device_id
    
    try:
        # Check if thing exists
        iot_client.describe_thing(thingName=thing_name)
        
        # Check if group exists
        iot_client.describe_thing_group(thingGroupName=group_name)
        
        # Add thing to group
        response = iot_client.add_thing_to_thing_group(
            thingName=thing_name,
            thingGroupName=group_name
        )
        print(f"Successfully added device {thing_name} to group {group_name}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Error: Either device {thing_name} or group {group_name} does not exist")
        else:
            print(f"Error adding device to group: {str(e)}")
        return False

def remove_device_from_group(device_id, group_name=None):
    """
    Removes a device from an IoT Thing Group
    
    Args:
        device_id (str): Device ID or Thing Name of the device
        group_name (str, optional): Name of the Thing Group. Defaults to CampoVisionDevices.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Initialize AWS IoT client
    iot_client = boto3.client('iot')
    
    # Default group name
    if not group_name:
        group_name = os.environ.get('IOT_THING_GROUP', 'CampoVisionDevices')
    
    # Prefix for thing name
    prefix = os.environ.get('THING_NAME_PREFIX', 'campo-vision-')
    
    # If device_id doesn't start with the prefix, add it
    if not device_id.startswith(prefix):
        thing_name = f"{prefix}{device_id}"
    else:
        thing_name = device_id
    
    try:
        # Remove thing from group
        response = iot_client.remove_thing_from_thing_group(
            thingName=thing_name,
            thingGroupName=group_name
        )
        print(f"Successfully removed device {thing_name} from group {group_name}")
        return True
    except ClientError as e:
        print(f"Error removing device from group: {str(e)}")
        return False

def list_devices_in_group(group_name=None):
    """
    Lists all devices in an IoT Thing Group
    
    Args:
        group_name (str, optional): Name of the Thing Group. Defaults to CampoVisionDevices.
    
    Returns:
        list: List of thing names in the group
    """
    # Initialize AWS IoT client
    iot_client = boto3.client('iot')
    
    # Default group name
    if not group_name:
        group_name = os.environ.get('IOT_THING_GROUP', 'CampoVisionDevices')
    
    try:
        # Check if group exists
        iot_client.describe_thing_group(thingGroupName=group_name)
        
        # List things in group
        response = iot_client.list_things_in_thing_group(
            thingGroupName=group_name,
            maxResults=100  # Adjust as needed
        )
        
        things = response.get('things', [])
        
        # Handle pagination if there are more results
        while 'nextToken' in response:
            response = iot_client.list_things_in_thing_group(
                thingGroupName=group_name,
                maxResults=100,
                nextToken=response['nextToken']
            )
            things.extend(response.get('things', []))
        
        if things:
            print(f"Devices in group {group_name}:")
            for thing in things:
                print(f"  - {thing}")
        else:
            print(f"No devices found in group {group_name}")
        
        return things
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Error: Group {group_name} does not exist")
        else:
            print(f"Error listing devices in group: {str(e)}")
        return []

def list_thing_groups():
    """
    Lists all IoT Thing Groups
    
    Returns:
        list: List of thing group names
    """
    # Initialize AWS IoT client
    iot_client = boto3.client('iot')
    
    try:
        # List thing groups
        response = iot_client.list_thing_groups(
            maxResults=100  # Adjust as needed
        )
        
        groups = response.get('thingGroups', [])
        
        # Handle pagination if there are more results
        while 'nextToken' in response:
            response = iot_client.list_thing_groups(
                maxResults=100,
                nextToken=response['nextToken']
            )
            groups.extend(response.get('thingGroups', []))
        
        if groups:
            print("IoT Thing Groups:")
            for group in groups:
                print(f"  - {group['groupName']}: {group['groupArn']}")
        else:
            print("No IoT Thing Groups found")
        
        return groups
    except ClientError as e:
        print(f"Error listing thing groups: {str(e)}")
        return []

def list_all_things():
    """
    Lists all IoT Things
    
    Returns:
        list: List of thing names
    """
    # Initialize AWS IoT client
    iot_client = boto3.client('iot')
    
    try:
        # List things
        response = iot_client.list_things(
            maxResults=100  # Adjust as needed
        )
        
        things = response.get('things', [])
        
        # Handle pagination if there are more results
        while 'nextToken' in response:
            response = iot_client.list_things(
                maxResults=100,
                nextToken=response['nextToken']
            )
            things.extend(response.get('things', []))
        
        return things
    except ClientError as e:
        print(f"Error listing things: {str(e)}")
        return []

def add_all_devices_to_group(group_name=None):
    """
    Adds all existing IoT Things to a Thing Group
    
    Args:
        group_name (str, optional): Name of the Thing Group. Defaults to CampoVisionDevices.
    
    Returns:
        tuple: (success_count, failure_count)
    """
    # Initialize AWS IoT client
    iot_client = boto3.client('iot')
    
    # Default group name
    if not group_name:
        group_name = os.environ.get('IOT_THING_GROUP', 'CampoVisionDevices')
    
    # Prefix for thing name
    prefix = os.environ.get('THING_NAME_PREFIX', 'campo-vision-')
    
    # Get all things
    things = list_all_things()
    
    success_count = 0
    failure_count = 0
    
    # Filter things that match our prefix
    campo_vision_things = [thing['thingName'] for thing in things 
                           if thing['thingName'].startswith(prefix)]
    
    if not campo_vision_things:
        print(f"No devices found with prefix '{prefix}'")
        return (0, 0)
    
    print(f"Found {len(campo_vision_things)} Campo Vision devices")
    
    # Add each thing to the group
    for thing_name in campo_vision_things:
        try:
            iot_client.add_thing_to_thing_group(
                thingName=thing_name,
                thingGroupName=group_name
            )
            print(f"Added {thing_name} to group {group_name}")
            success_count += 1
        except ClientError as e:
            print(f"Failed to add {thing_name} to group: {str(e)}")
            failure_count += 1
    
    print(f"Summary: Added {success_count} devices to group {group_name}, {failure_count} failures")
    return (success_count, failure_count)

def main():
    parser = argparse.ArgumentParser(description='Manage AWS IoT Thing Groups for Campo Vision devices')
    
    # Group management options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--add-device', help='Add a device to a thing group')
    group.add_argument('--remove-device', help='Remove a device from a thing group')
    group.add_argument('--list-devices', action='store_true', help='List devices in a thing group')
    group.add_argument('--list-groups', action='store_true', help='List all thing groups')
    group.add_argument('--add-all-devices', action='store_true', help='Add all existing devices to a thing group')
    
    # Optional arguments
    parser.add_argument('--group-name', help='Name of the thing group (default: CampoVisionDevices)')
    
    args = parser.parse_args()
    
    # Execute requested action
    if args.add_device:
        add_device_to_group(args.add_device, args.group_name)
    elif args.remove_device:
        remove_device_from_group(args.remove_device, args.group_name)
    elif args.list_devices:
        list_devices_in_group(args.group_name)
    elif args.list_groups:
        list_thing_groups()
    elif args.add_all_devices:
        add_all_devices_to_group(args.group_name)

if __name__ == "__main__":
    main()
