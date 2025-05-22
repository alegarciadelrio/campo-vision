import json
import boto3
import os
import logging
import sys
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
from decimal import Decimal

# Add the common directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import auth

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
# Check if running locally
endpoint_url = None
if 'AWS_SAM_LOCAL' in os.environ or 'LAMBDA_TASK_ROOT' not in os.environ:
    # Local development
    endpoint_url = 'http://localhost:8000'
    logger.info(f"Using local DynamoDB endpoint: {endpoint_url}")

dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
table_name = os.environ.get('TELEMETRY_TABLE', 'TelemetryTable')

# Make sure table_name is not None
if not table_name:
    table_name = 'TelemetryTable'
    
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Retrieves telemetry data from DynamoDB based on query parameters
    
    Supported query parameters:
    - deviceId: Filter by specific device ID (required)
    - startTime: ISO8601 timestamp for start of time range
    - endTime: ISO8601 timestamp for end of time range
    - limit: Maximum number of records to return (default: 100)
    
    Requires authentication via Cognito JWT token in the Authorization header
    """
    # Check authentication
    auth_error = auth.require_auth(event)
    if auth_error:
        return auth_error
        
    # Get authenticated user
    user = auth.get_user_from_event(event)
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        
        # Check for required deviceId
        if 'deviceId' not in query_params:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameter: deviceId'
                })
            }
        
        device_id = query_params['deviceId']
        
        # Build query parameters
        query_kwargs = {
            'KeyConditionExpression': Key('deviceId').eq(device_id)
        }
        
        # Add time range if specified
        if 'startTime' in query_params and 'endTime' in query_params:
            start_time = query_params['startTime']
            end_time = query_params['endTime']
            query_kwargs['KeyConditionExpression'] = Key('deviceId').eq(device_id) & \
                                                    Key('timestamp').between(start_time, end_time)
        elif 'startTime' in query_params:
            start_time = query_params['startTime']
            query_kwargs['KeyConditionExpression'] = Key('deviceId').eq(device_id) & \
                                                    Key('timestamp').gte(start_time)
        elif 'endTime' in query_params:
            end_time = query_params['endTime']
            query_kwargs['KeyConditionExpression'] = Key('deviceId').eq(device_id) & \
                                                    Key('timestamp').lte(end_time)
        
        # Set limit if specified
        if 'limit' in query_params:
            try:
                limit = int(query_params['limit'])
                query_kwargs['Limit'] = limit
            except ValueError:
                logger.warning(f"Invalid limit parameter: {query_params['limit']}")
        
        # Query DynamoDB
        response = table.query(**query_kwargs)
        items = response.get('Items', [])
        
        logger.info(f"Retrieved {len(items)} telemetry records for device {device_id}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'deviceId': device_id,
                'count': len(items),
                'telemetry': items
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving telemetry data: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            }, cls=DecimalEncoder)
        }
