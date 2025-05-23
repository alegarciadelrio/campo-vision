import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
from decimal import Decimal

# Import auth module from Lambda layer
import auth

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB resources

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

# Trigger redeployment and improve error handling for authentication
def lambda_handler(event, context):
    """
    Handles requests to retrieve telemetry data from DynamoDB
    
    Query parameters:
    - deviceId: Filter by device ID (required)
    - startTime: Filter by start time (ISO 8601 format, optional)
    - endTime: Filter by end time (ISO 8601 format, optional)
    """
    try:
        # Log the incoming event for debugging
        logger.info(f"Received event: {event}")
        
        # Check if this is an OPTIONS request (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({})
            }
            
        # Validate JWT token
        try:
            claims = auth.require_auth(event)
            logger.info(f"Authenticated user: {claims.get('username') if claims else 'None'} (CORS preflight)")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Unauthorized',
                    'message': str(e)
                }, cls=DecimalEncoder)
            }
        
        # Get query parameters
        query_params = event.get('queryStringParameters', {})
        if not query_params:
            logger.error("Missing query parameters")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({
                    'error': 'Missing query parameters'
                })
            }
            
        logger.info(f"Query parameters: {query_params}")
        
        # Check for required deviceId
        if 'deviceId' not in query_params:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
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
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'deviceId': device_id,
                'count': len(items),
                'telemetry': items
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving telemetry data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            }, cls=DecimalEncoder)
        }
