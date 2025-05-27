import json
import os
import uuid
import boto3
import logging
from datetime import datetime
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
device_table = dynamodb.Table(os.environ.get('DEVICE_TABLE'))

def lambda_handler(event, context):
    """
    Lambda function to manage devices (create, update, delete)
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Handle different HTTP methods
    http_method = event.get('httpMethod', '')
    
    if http_method == 'OPTIONS':
        # Handle CORS preflight request
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({})
        }
    
    # Extract user information from the request
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    claims = authorizer.get('claims', {})
    user_id = claims.get('sub', '')
    
    if not user_id:
        logger.error("User ID not found in the request")
        return {
            'statusCode': 401,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    if http_method == 'POST':
        # Create a new device
        return register_device(event, user_id)
    elif http_method == 'GET':
        # Get device details
        return get_device(event)
    elif http_method == 'PUT':
        # Update device details
        return update_device(event, user_id)
    elif http_method == 'DELETE':
        # Delete a device
        return delete_device(event, user_id)
    else:
        logger.error(f"Unsupported HTTP method: {http_method}")
        return {
            'statusCode': 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Unsupported HTTP method: {http_method}'})
        }

def register_device(event, user_id):
    """
    Register a new device
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        device_id = body.get('deviceId')
        company_id = body.get('companyId')
        
        if not device_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Device ID is required'})
            }
        
        if not company_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Company ID is required'})
            }
        
        # Check if device already exists
        try:
            response = device_table.get_item(Key={'deviceId': device_id})
            if 'Item' in response:
                return {
                    'statusCode': 409,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': f'Device with ID {device_id} already exists'})
                }
        except ClientError as e:
            logger.error(f"Error checking device existence: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Error checking device existence'})
            }
        
        # Create device item
        timestamp = datetime.utcnow().isoformat()
        device_item = {
            'deviceId': device_id,
            'companyId': company_id,
            'name': body.get('name', ''),
            'description': body.get('description', ''),
            'createdBy': user_id,
            'createdAt': timestamp,
            'updatedAt': timestamp
        }
        
        # Save to DynamoDB
        device_table.put_item(Item=device_item)
        
        return {
            'statusCode': 201,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Device registered successfully',
                'device': device_item
            })
        }
    
    except Exception as e:
        logger.error(f"Error registering device: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Error registering device: {str(e)}'})
        }

def get_device(event):
    """
    Get device details
    """
    try:
        # Get device ID from query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        device_id = query_params.get('deviceId')
        
        if not device_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Device ID is required'})
            }
        
        # Get device from DynamoDB
        response = device_table.get_item(Key={'deviceId': device_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'Device with ID {device_id} not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'device': response['Item']})
        }
    
    except Exception as e:
        logger.error(f"Error getting device: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Error getting device: {str(e)}'})
        }

def update_device(event, user_id):
    """
    Update device details
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        device_id = body.get('deviceId')
        
        if not device_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Device ID is required'})
            }
        
        # Check if device exists
        response = device_table.get_item(Key={'deviceId': device_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'Device with ID {device_id} not found'})
            }
        
        # Update device item
        existing_device = response['Item']
        timestamp = datetime.utcnow().isoformat()
        
        update_expression = "SET updatedAt = :updatedAt"
        expression_attribute_values = {
            ':updatedAt': timestamp
        }
        
        # Update fields if provided
        if 'name' in body:
            update_expression += ", #name = :name"
            expression_attribute_values[':name'] = body['name']
        
        if 'description' in body:
            update_expression += ", description = :description"
            expression_attribute_values[':description'] = body['description']
        
        # Update in DynamoDB
        response = device_table.update_item(
            Key={'deviceId': device_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames={'#name': 'name'} if 'name' in body else {},
            ReturnValues="ALL_NEW"
        )
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Device updated successfully',
                'device': response.get('Attributes', {})
            })
        }
    
    except Exception as e:
        logger.error(f"Error updating device: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Error updating device: {str(e)}'})
        }

def delete_device(event, user_id):
    """
    Delete a device
    """
    try:
        # Get device ID from query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        device_id = query_params.get('deviceId')
        
        if not device_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Device ID is required'})
            }
        
        # Check if device exists
        response = device_table.get_item(Key={'deviceId': device_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'Device with ID {device_id} not found'})
            }
        
        # Delete from DynamoDB
        device_table.delete_item(Key={'deviceId': device_id})
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'message': 'Device deleted successfully'})
        }
    
    except Exception as e:
        logger.error(f"Error deleting device: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Error deleting device: {str(e)}'})
        }
