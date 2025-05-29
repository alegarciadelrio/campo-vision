import json
import os
import uuid
import boto3
import logging
from datetime import datetime
from auth import validate_token, get_user_id_from_token

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
company_table = dynamodb.Table(os.environ.get('COMPANY_TABLE'))
user_company_table = dynamodb.Table(os.environ.get('USER_COMPANY_TABLE'))

def lambda_handler(event, context):
    """
    Lambda function to manage companies
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Define CORS headers to be used in all responses
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    # Handle OPTIONS request for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({})
        }
    
    # Validate token for non-OPTIONS requests
    try:
        headers = event.get('headers', {})
        if not headers:
            headers = {}
            
        auth_header = headers.get('Authorization', '')
        if not auth_header:
            auth_header = headers.get('authorization', '')
            
        token = auth_header.replace('Bearer ', '') if auth_header else ''
        claims = validate_token(token)
        user_id = get_user_id_from_token(claims)
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return {
            'statusCode': 401,
            'headers': cors_headers,
            'body': json.dumps({
                'message': f'Unauthorized: {str(e)}'
            })
        }
    
    # Handle different HTTP methods
    if event.get('httpMethod') == 'GET':
        return get_company(event, user_id, cors_headers)
    elif event.get('httpMethod') == 'POST':
        return create_company(event, user_id, cors_headers)
    elif event.get('httpMethod') == 'PUT':
        return update_company(event, user_id, cors_headers)
    elif event.get('httpMethod') == 'DELETE':
        return delete_company(event, user_id, cors_headers)
    else:
        headers = cors_headers.copy()
        headers['Content-Type'] = 'application/json'
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'message': 'Unsupported HTTP method'
            })
        }

def get_company(event, user_id, cors_headers):
    """
    Get company details
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        company_id = query_params.get('companyId')
        
        # Prepare headers with content type
        headers = cors_headers.copy()
        headers['Content-Type'] = 'application/json'
        
        if company_id:
            # Get specific company
            response = company_table.get_item(
                Key={'companyId': company_id}
            )
            company = response.get('Item')
            
            if not company:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({
                        'message': 'Company not found'
                    })
                }
                
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'company': company
                })
            }
        else:
            # Get all companies for the user
            # This is a simplified approach - in a real app, you might want to use a query with GSI
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Company ID is required'
                })
            }
    except Exception as e:
        logger.error(f"Error getting company: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': f'Error getting company: {str(e)}'
            })
        }

def create_company(event, user_id, cors_headers):
    """
    Create a new company and associate it with the user
    """
    try:
        # Prepare headers with content type
        headers = cors_headers.copy()
        headers['Content-Type'] = 'application/json'
        
        # Parse request body
        body_str = event.get('body', '{}')
        body = json.loads(body_str) if body_str else {}
        company_name = body.get('name')
        description = body.get('description', '')
        
        if not company_name:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Company name is required'
                })
            }
        
        # Generate a unique company ID
        company_id = f"comp-{str(uuid.uuid4())}"
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create company in DynamoDB
        company = {
            'companyId': company_id,
            'name': company_name,
            'description': description,
            'createdBy': user_id,
            'createdAt': timestamp,
            'updatedAt': timestamp
        }
        
        company_table.put_item(Item=company)
        
        # Associate user with company (as admin)
        user_company = {
            'userId': user_id,
            'companyId': company_id,
            'role': 'admin',
            'createdAt': timestamp
        }
        
        user_company_table.put_item(Item=user_company)
        
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'message': 'Company created successfully',
                'company': company
            })
        }
    except Exception as e:
        logger.error(f"Error creating company: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': f'Error creating company: {str(e)}'
            })
        }

def update_company(event, user_id, cors_headers):
    """
    Update company details
    """
    try:
        # Prepare headers with content type
        headers = cors_headers.copy()
        headers['Content-Type'] = 'application/json'
        
        # Parse request body
        body_str = event.get('body', '{}')
        body = json.loads(body_str) if body_str else {}
        company_id = body.get('companyId')
        company_name = body.get('name')
        description = body.get('description')
        
        if not company_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Company ID is required'
                })
            }
        
        # Check if the user has admin rights for this company
        user_company_response = user_company_table.get_item(
            Key={
                'userId': user_id,
                'companyId': company_id
            }
        )
        
        user_company = user_company_response.get('Item')
        if not user_company or user_company.get('role') != 'admin':
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'message': 'You do not have permission to update this company'
                })
            }
        
        # Update company in DynamoDB
        update_expression = "SET updatedAt = :updatedAt"
        expression_values = {
            ':updatedAt': datetime.utcnow().isoformat() + 'Z'
        }
        
        if company_name:
            update_expression += ", #name = :name"
            expression_values[':name'] = company_name
        
        if description is not None:
            update_expression += ", description = :description"
            expression_values[':description'] = description
        
        response = company_table.update_item(
            Key={'companyId': company_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames={'#name': 'name'} if company_name else {},
            ReturnValues="ALL_NEW"
        )
        
        updated_company = response.get('Attributes', {})
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Company updated successfully',
                'company': updated_company
            })
        }
    except Exception as e:
        logger.error(f"Error updating company: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': f'Error updating company: {str(e)}'
            })
        }

def delete_company(event, user_id, cors_headers):
    """
    Delete a company
    """
    try:
        # Prepare headers with content type
        headers = cors_headers.copy()
        headers['Content-Type'] = 'application/json'
        
        # Parse request body
        body_str = event.get('body', '{}')
        body = json.loads(body_str) if body_str else {}
        company_id = body.get('companyId')
        
        if not company_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Company ID is required'
                })
            }
        
        # Check if the user has admin rights for this company
        user_company_response = user_company_table.get_item(
            Key={
                'userId': user_id,
                'companyId': company_id
            }
        )
        
        user_company = user_company_response.get('Item')
        if not user_company or user_company.get('role') != 'admin':
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({
                    'message': 'You do not have permission to delete this company'
                })
            }
        
        # Query all user-company associations for this company
        user_company_associations = []
        response = user_company_table.query(
            IndexName='CompanyIndex',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('companyId').eq(company_id)
        )
        user_company_associations.extend(response.get('Items', []))
        
        # Continue querying if there are more results (pagination)
        while 'LastEvaluatedKey' in response:
            response = user_company_table.query(
                IndexName='CompanyIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('companyId').eq(company_id),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            user_company_associations.extend(response.get('Items', []))
        
        # Delete all user-company associations for this company
        for association in user_company_associations:
            user_company_table.delete_item(
                Key={
                    'userId': association['userId'],
                    'companyId': company_id
                }
            )
            logger.info(f"Deleted user-company association for user {association['userId']} and company {company_id}")
        
        # Delete company from DynamoDB
        company_table.delete_item(
            Key={'companyId': company_id}
        )
        
        # Note: In a real application, you would also need to:
        # 1. Handle or delete all telemetry data associated with this company's devices
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Company deleted successfully'
            })
        }
    except Exception as e:
        logger.error(f"Error deleting company: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': f'Error deleting company: {str(e)}'
            })
        }
