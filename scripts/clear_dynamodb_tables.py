#!/usr/bin/env python3
"""
Script to clear all data from DynamoDB tables in the Campo Vision project.

This script will:
1. List all available DynamoDB tables in your AWS account
2. Allow you to select which tables to clear
3. Remove all items from the selected tables

Usage:
    python clear_dynamodb_tables.py [--profile PROFILE] [--region REGION] [--list-only]
    python clear_dynamodb_tables.py [--profile PROFILE] [--region REGION] --tables TABLE1 TABLE2

Options:
    --profile PROFILE    AWS profile to use
    --region REGION      AWS region to use (default: us-east-1)
    --list-only          Only list available tables without clearing any data
    --tables TABLE1 ...  Specific tables to clear (space-separated)
"""

import argparse
import boto3
import time
import sys
import re
from botocore.exceptions import ClientError


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Clear all data from DynamoDB tables.')
    parser.add_argument('--profile', help='AWS profile to use')
    parser.add_argument('--region', default='us-east-1', help='AWS region to use')
    parser.add_argument('--list-only', action='store_true', help='Only list available tables without clearing any data')
    parser.add_argument('--tables', nargs='+', help='Specific tables to clear (space-separated)')
    return parser.parse_args()


def list_dynamodb_tables(dynamodb_client):
    """
    List all DynamoDB tables in the AWS account.
    
    Args:
        dynamodb_client: DynamoDB client
        
    Returns:
        List of table names
    """
    tables = []
    last_evaluated_table_name = None
    
    while True:
        if last_evaluated_table_name:
            response = dynamodb_client.list_tables(ExclusiveStartTableName=last_evaluated_table_name)
        else:
            response = dynamodb_client.list_tables()
            
        tables.extend(response.get('TableNames', []))
        
        last_evaluated_table_name = response.get('LastEvaluatedTableName')
        if not last_evaluated_table_name:
            break
    
    return tables


def filter_campo_vision_tables(tables):
    """
    Filter tables that are likely part of the Campo Vision project.
    
    Args:
        tables: List of all table names
        
    Returns:
        List of Campo Vision table names
    """
    # Patterns to look for in table names
    patterns = [
        r'.*telemetry.*',
        r'.*company.*',
        r'.*device.*',
        r'.*user.*company.*',
        r'.*campo.*vision.*'
    ]
    
    campo_vision_tables = []
    
    for table in tables:
        for pattern in patterns:
            if re.search(pattern, table.lower()):
                campo_vision_tables.append(table)
                break
    
    return campo_vision_tables


def select_tables_to_clear(all_tables, campo_vision_tables, specified_tables=None):
    """
    Allow user to select which tables to clear.
    
    Args:
        all_tables: List of all table names
        campo_vision_tables: List of Campo Vision table names
        specified_tables: List of tables specified via command line
        
    Returns:
        List of tables to clear
    """
    if specified_tables:
        # Verify that specified tables exist
        tables_to_clear = []
        for table in specified_tables:
            if table in all_tables:
                tables_to_clear.append(table)
            else:
                print(f"Warning: Table '{table}' not found in your AWS account")
        
        if not tables_to_clear:
            print("None of the specified tables were found in your AWS account")
            sys.exit(1)
            
        return tables_to_clear
    
    # If no tables specified, prompt user to select from Campo Vision tables
    if not campo_vision_tables:
        print("No Campo Vision related tables found in your AWS account")
        print("\nAll available tables:")
        for i, table in enumerate(all_tables, 1):
            print(f"{i}. {table}")
            
        selection = input("\nEnter table numbers to clear (comma-separated) or 'all' for all tables: ")
        
        if selection.lower() == 'all':
            return all_tables
        
        try:
            indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
            return [all_tables[idx] for idx in indices if 0 <= idx < len(all_tables)]
        except (ValueError, IndexError):
            print("Invalid selection")
            sys.exit(1)
    
    # Display Campo Vision tables with indices
    print("Found the following Campo Vision related tables:")
    for i, table in enumerate(campo_vision_tables, 1):
        print(f"{i}. {table}")
        
    selection = input("\nEnter table numbers to clear (comma-separated) or 'all' for all tables\nor 'more' to see all tables in your account: ")
    
    if selection.lower() == 'more':
        print("\nAll available tables:")
        for i, table in enumerate(all_tables, 1):
            print(f"{i}. {table}")
            
        selection = input("\nEnter table numbers to clear (comma-separated) or 'all' for all tables: ")
    
    if selection.lower() == 'all':
        return campo_vision_tables
    
    try:
        indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
        return [campo_vision_tables[idx] for idx in indices if 0 <= idx < len(campo_vision_tables)]
    except (ValueError, IndexError):
        print("Invalid selection")
        sys.exit(1)


def clear_table(dynamodb, table_name):
    """
    Clear all items from the specified DynamoDB table.
    
    Args:
        dynamodb: DynamoDB resource
        table_name: Name of the table to clear
    """
    try:
        table = dynamodb.Table(table_name)
        
        # Get the table's key schema
        key_schema = table.key_schema
        if not key_schema:
            print(f"Could not retrieve key schema for table {table_name}")
            return False
        
        # Get the names of the key attributes
        hash_key = next((item['AttributeName'] for item in key_schema if item['KeyType'] == 'HASH'), None)
        range_key = next((item['AttributeName'] for item in key_schema if item['KeyType'] == 'RANGE'), None)
        
        if not hash_key:
            print(f"Could not identify hash key for table {table_name}")
            return False
        
        # Scan the table to get all items
        print(f"Scanning table {table_name}...")
        items = []
        scan_kwargs = {}
        done = False
        start_time = time.time()
        
        while not done:
            response = table.scan(**scan_kwargs)
            items.extend(response.get('Items', []))
            
            # Print progress
            print(f"Retrieved {len(items)} items so far...")
            
            if 'LastEvaluatedKey' not in response:
                done = True
            else:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        
        total_items = len(items)
        print(f"Found {total_items} items in {table_name}")
        
        if total_items == 0:
            print(f"Table {table_name} is already empty")
            return True
        
        # Delete all items
        print(f"Deleting {total_items} items from {table_name}...")
        deleted = 0
        batch_size = 25  # Maximum batch size for BatchWriteItem
        
        for i in range(0, total_items, batch_size):
            batch = items[i:i + batch_size]
            batch_request = []
            
            for item in batch:
                delete_request = {'DeleteRequest': {'Key': {}}}
                delete_request['DeleteRequest']['Key'][hash_key] = item[hash_key]
                
                if range_key and range_key in item:
                    delete_request['DeleteRequest']['Key'][range_key] = item[range_key]
                
                batch_request.append(delete_request)
            
            response = dynamodb.batch_write_item(
                RequestItems={
                    table_name: batch_request
                }
            )
            
            # Handle unprocessed items
            unprocessed = response.get('UnprocessedItems', {}).get(table_name, [])
            if unprocessed:
                print(f"Warning: {len(unprocessed)} items were not processed in this batch")
            
            deleted += len(batch) - len(unprocessed)
            print(f"Deleted {deleted}/{total_items} items...")
        
        elapsed_time = time.time() - start_time
        print(f"Successfully cleared table {table_name} in {elapsed_time:.2f} seconds")
        return True
    
    except ClientError as e:
        print(f"Error clearing table {table_name}: {e}")
        return False


def main():
    """Main function."""
    args = parse_args()
    
    # Create a session with the specified profile and region
    session_kwargs = {'region_name': args.region}
    if args.profile:
        session_kwargs['profile_name'] = args.profile
    
    session = boto3.Session(**session_kwargs)
    dynamodb = session.resource('dynamodb')
    dynamodb_client = session.client('dynamodb')
    
    # List all tables in the account
    print("Listing DynamoDB tables...")
    all_tables = list_dynamodb_tables(dynamodb_client)
    
    if not all_tables:
        print("No DynamoDB tables found in your AWS account")
        sys.exit(1)
        
    # Filter tables that are likely part of Campo Vision
    campo_vision_tables = filter_campo_vision_tables(all_tables)
    
    # If list-only flag is set, just list the tables and exit
    if args.list_only:
        print(f"\nFound {len(all_tables)} DynamoDB tables in your AWS account:")
        for table in all_tables:
            print(f"  - {table}")
            
        if campo_vision_tables:
            print(f"\nPotential Campo Vision tables ({len(campo_vision_tables)}):")
            for table in campo_vision_tables:
                print(f"  - {table}")
        else:
            print("\nNo potential Campo Vision tables identified")
            
        sys.exit(0)
    
    # Select tables to clear
    tables_to_clear = select_tables_to_clear(all_tables, campo_vision_tables, args.tables)
    
    if not tables_to_clear:
        print("No tables selected for clearing")
        sys.exit(0)
        
    # Confirm before clearing
    print(f"\nYou are about to clear ALL DATA from the following tables:")
    for table in tables_to_clear:
        print(f"  - {table}")
        
    confirmation = input("\nAre you sure you want to proceed? This action cannot be undone. (yes/no): ")
    
    if confirmation.lower() != 'yes':
        print("Operation cancelled")
        sys.exit(0)
    
    # Clear each selected table
    success = True
    for table_name in tables_to_clear:
        print(f"\n{'=' * 50}")
        print(f"Processing table: {table_name}")
        print(f"{'=' * 50}")
        
        if not clear_table(dynamodb, table_name):
            success = False
    
    if success:
        print("\nAll selected tables have been successfully cleared.")
    else:
        print("\nSome tables could not be cleared. Check the output for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
