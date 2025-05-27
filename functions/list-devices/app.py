import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key, Attr
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
endpoint_url = None
if 'AWS_SAM_LOCAL' in os.environ or 'LAMBDA_TASK_ROOT' not in os.environ:
    # Local development
    endpoint_url = 'http://localhost:8000'
    logger.info(f"Using local DynamoDB endpoint: {endpoint_url}")

dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
device_table_name = os.environ.get('DEVICE_TABLE', 'DeviceTable')
telemetry_table_name = os.environ.get('TELEMETRY_TABLE', 'TelemetryTable')

# Make sure table names are not None
if not device_table_name:
    device_table_name = 'DeviceTable'
if not telemetry_table_name:
    telemetry_table_name = 'TelemetryTable'
    
device_table = dynamodb.Table(device_table_name)
telemetry_table = dynamodb.Table(telemetry_table_name)

def lambda_handler(event, context):
    """
    Handles requests to retrieve a list of all devices
    
    Query parameters:
    - companyId: Filter by company ID (optional)
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
                    'Access-Control-Allow-Methods': 'OPTIONS,GET'
                },
                'body': json.dumps({})
            }
            
        # Validate JWT token
        try:
            claims = auth.require_auth(event)
            logger.info(f"Authenticated user: {claims.get('username') if claims else 'None'}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET'
                },
                'body': json.dumps({
                    'error': 'Unauthorized',
                    'message': str(e)
                }, cls=DecimalEncoder)
            }
        
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        logger.info(f"Query parameters: {query_params}")
        
        # Get all devices from the device table
        if 'companyId' in query_params:
            # Filter by company ID if provided
            company_id = query_params['companyId']
            response = device_table.query(
                IndexName="CompanyIndex",
                KeyConditionExpression=Key('companyId').eq(company_id)
            )
        else:
            # Get all devices if no company ID is provided
            response = device_table.scan()
            
        devices = response.get('Items', [])
        
        # For each device, get the latest telemetry data
        for device in devices:
            device_id = device['deviceId']
            try:
                # Query the telemetry table to get the latest entry for this device
                telemetry_response = telemetry_table.query(
                    KeyConditionExpression=Key('deviceId').eq(device_id),
                    ScanIndexForward=False,  # Sort in descending order (newest first)
                    Limit=1  # Get only the latest record
                )
                
                latest_telemetry = telemetry_response.get('Items', [])
                if latest_telemetry:
                    device['lastTelemetry'] = latest_telemetry[0]
                else:
                    device['lastTelemetry'] = None
            except Exception as e:
                logger.error(f"Error getting latest telemetry for device {device_id}: {str(e)}")
                device['lastTelemetry'] = None
                
        logger.info(f"Retrieved {len(devices)} devices")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({
                'count': len(devices),
                'devices': devices
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving devices: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            }, cls=DecimalEncoder)
        }
