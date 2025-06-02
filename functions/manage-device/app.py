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

# Initialize AWS IoT client
iot_client = boto3.client('iot')

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
    Register a new device in DynamoDB and AWS IoT
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
        
        # Register device in AWS IoT
        iot_registration_success = True
        iot_error_message = None
        try:
            # Create a thing in AWS IoT
            thing_response = iot_client.create_thing(
                thingName=device_id,
                attributePayload={
                    'attributes': {
                        'companyId': company_id,
                        'name': body.get('name', ''),
                        'description': body.get('description', '')
                    }
                }
            )
            logger.info(f"Successfully registered device {device_id} in AWS IoT: {thing_response}")
        except ClientError as e:
            iot_registration_success = False
            iot_error_message = str(e)
            logger.error(f"Error registering device in AWS IoT: {iot_error_message}")
            # We continue with the operation as the device is already in DynamoDB
        
        response_message = 'Device registered successfully'
        if not iot_registration_success:
            response_message += f', but failed to register in AWS IoT: {iot_error_message}'
        
        return {
            'statusCode': 201,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': response_message,
                'device': device_item,
                'iotRegistrationSuccess': iot_registration_success
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
    Delete a device from DynamoDB and AWS IoT
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
        
        # Delete from AWS IoT
        try:
            # First, find all principals (certificates) attached to the thing
            principals = []
            try:
                principals_response = iot_client.list_thing_principals(thingName=device_id)
                principals = principals_response.get('principals', [])
                logger.info(f"Found {len(principals)} principals attached to device {device_id}")
            except ClientError as e:
                logger.warning(f"Error listing principals for device {device_id}: {str(e)}")
            
            # Detach and delete each principal (certificate)
            for principal in principals:
                try:
                    # Get certificate ID from ARN
                    cert_id = principal.split('/')[-1]
                    
                    # Detach the certificate from the thing
                    logger.info(f"Detaching certificate {cert_id} from device {device_id}")
                    iot_client.detach_thing_principal(
                        thingName=device_id,
                        principal=principal
                    )
                    
                    # Find and detach any policies attached to the certificate
                    try:
                        policies_response = iot_client.list_attached_policies(
                            target=principal
                        )
                        
                        for policy in policies_response.get('policies', []):
                            policy_name = policy.get('policyName')
                            logger.info(f"Detaching policy {policy_name} from certificate {cert_id}")
                            iot_client.detach_policy(
                                policyName=policy_name,
                                target=principal
                            )
                    except ClientError as e:
                        logger.warning(f"Error detaching policies from certificate {cert_id}: {str(e)}")
                    
                    # Deactivate the certificate
                    logger.info(f"Deactivating certificate {cert_id}")
                    iot_client.update_certificate(
                        certificateId=cert_id,
                        newStatus='INACTIVE'
                    )
                    
                    # Delete the certificate
                    logger.info(f"Deleting certificate {cert_id}")
                    iot_client.delete_certificate(
                        certificateId=cert_id,
                        forceDelete=True
                    )
                except ClientError as e:
                    logger.warning(f"Error processing certificate {principal}: {str(e)}")
            
            # Now delete the thing
            iot_client.delete_thing(thingName=device_id)
            logger.info(f"Successfully deleted device {device_id} from AWS IoT")
        except ClientError as e:
            # If the thing doesn't exist in IoT, log the error but don't fail the operation
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'ResourceNotFoundException':
                logger.warning(f"Device {device_id} not found in AWS IoT, continuing with deletion")
            else:
                logger.error(f"Error deleting device from AWS IoT: {str(e)}")
                # We don't return an error here as we've already deleted from DynamoDB
                # and we want the operation to be considered successful
        
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
