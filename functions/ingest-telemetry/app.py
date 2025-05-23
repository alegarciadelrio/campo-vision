import json
import boto3
import os
import logging
from datetime import datetime
from decimal import Decimal

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
    Handles incoming telemetry data and stores it in DynamoDB
    
    Expected JSON format:
    {
        "deviceId": "device123",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "temperature": 25.5,
        "timestamp": "2023-05-22T14:30:00Z" (optional, will use current time if not provided)
    }
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
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({})
            }
        
        # Parse request body
        if not event.get('body'):
            logger.error("Missing request body")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing request body'
                })
            }
            
        try:
            request_body = json.loads(event['body'])
            logger.info(f"Request body: {request_body}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing request body: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Invalid JSON in request body: {str(e)}'
                })
            }
        
        # Validate required fields
        required_fields = ['deviceId', 'latitude', 'longitude', 'temperature']
        for field in required_fields:
            if field not in request_body:
                logger.error(f"Missing required field: {field}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'Missing required field: {field}'
                    })
                }
        
        # Extract telemetry data
        device_id = request_body['deviceId']
        latitude = request_body['latitude']
        longitude = request_body['longitude']
        temperature = request_body['temperature']
        
        # Use provided timestamp or current time
        if 'timestamp' in request_body:
            timestamp = request_body['timestamp']
        else:
            timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create item for DynamoDB
        telemetry_item = {
            'deviceId': device_id,
            'timestamp': timestamp,
            'latitude': Decimal(str(latitude)),
            'longitude': Decimal(str(longitude)),
            'temperature': Decimal(str(temperature))
        }
        
        # Add optional fields if present
        for key, value in request_body.items():
            if key not in telemetry_item:
                # Convert float values to Decimal for DynamoDB
                if isinstance(value, float):
                    telemetry_item[key] = Decimal(str(value))
                else:
                    telemetry_item[key] = value
        
        # Store in DynamoDB
        table.put_item(Item=telemetry_item)
        
        logger.info(f"Stored telemetry data for device {device_id}")
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Telemetry data stored successfully',
                'deviceId': device_id,
                'timestamp': timestamp
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing telemetry data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
