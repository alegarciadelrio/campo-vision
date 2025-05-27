import json
import boto3
import os
import logging
import datetime
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
user_company_table_name = os.environ.get('USER_COMPANY_TABLE', 'UserCompanyTable')
company_table_name = os.environ.get('COMPANY_TABLE', 'CompanyTable')

# Make sure table names are not None
if not user_company_table_name:
    user_company_table_name = 'UserCompanyTable'
if not company_table_name:
    company_table_name = 'CompanyTable'
    
# Log table names for debugging
logger.info(f"USER_COMPANY_TABLE: {user_company_table_name}")
logger.info(f"COMPANY_TABLE: {company_table_name}")
    
user_company_table = dynamodb.Table(user_company_table_name)
company_table = dynamodb.Table(company_table_name)

# Initialize Cognito client
cognito = boto3.client('cognito-idp', endpoint_url=endpoint_url)
user_pool_id = os.environ.get('USER_POOL_ID')

# Log user pool ID for debugging
logger.info(f"USER_POOL_ID: {user_pool_id}")

def lambda_handler(event, context):
    """
    Handles requests to manage user-company relationships
    
    Operations:
    - GET: Get companies for a user or users for a company
    - POST: Assign a user to a company
    - DELETE: Remove a user from a company
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
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,DELETE'
                },
                'body': json.dumps({})
            }
            
        # Validate JWT token
        try:
            claims = auth.require_auth(event)
            logger.info(f"Authenticated user: {claims.get('username') if claims else 'None'}")
            
            # Check if user is an admin (for operations that require admin privileges)
            # This is a simple example - you might want to use Cognito groups for a more robust approach
            is_admin = is_admin_user(claims)
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,DELETE'
                },
                'body': json.dumps({
                    'error': 'Unauthorized',
                    'message': str(e)
                }, cls=DecimalEncoder)
            }
        
        # Handle different HTTP methods
        http_method = event.get('httpMethod')
        
        if http_method == 'GET':
            return handle_get_request(event, claims, is_admin)
        elif http_method == 'POST':
            return handle_post_request(event, claims, is_admin)
        elif http_method == 'DELETE':
            return handle_delete_request(event, claims, is_admin)
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,DELETE'
                },
                'body': json.dumps({
                    'error': 'Invalid HTTP method',
                    'message': f'Method {http_method} not supported'
                })
            }
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,DELETE'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            }, cls=DecimalEncoder)
        }

def handle_get_request(event, claims, is_admin):
    """
    Handle GET requests to retrieve user-company relationships
    
    Query parameters:
    - userId: Get companies for this user
    - companyId: Get users for this company
    """
    query_params = event.get('queryStringParameters', {}) or {}
    
    # Get the authenticated user's ID
    authenticated_user_id = claims.get('sub')
    
    if 'userId' in query_params:
        # Get companies for a specific user
        user_id = query_params['userId']
        
        # Only allow users to query their own data unless they're admins
        if user_id != authenticated_user_id and not is_admin:
            return create_error_response(403, 'Forbidden', 'You can only query your own user-company relationships')
        
        # Query the UserCompany table
        response = user_company_table.query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        
        # Get company details for each company ID
        companies = []
        for item in response.get('Items', []):
            company_id = item.get('companyId')
            company_response = company_table.get_item(
                Key={'companyId': company_id}
            )
            company = company_response.get('Item')
            if company:
                companies.append(company)
        
        return create_success_response({
            'userId': user_id,
            'companies': companies
        })
        
    elif 'companyId' in query_params:
        # Get users for a specific company
        company_id = query_params['companyId']
        
        # Check if the authenticated user belongs to this company or is an admin
        if not is_admin and not user_belongs_to_company(authenticated_user_id, company_id):
            return create_error_response(403, 'Forbidden', 'You can only query companies you belong to')
        
        # Query the UserCompany table using the GSI
        response = user_company_table.query(
            IndexName="CompanyIndex",
            KeyConditionExpression=Key('companyId').eq(company_id)
        )
        
        # Get user details from Cognito for each user ID
        users = []
        for item in response.get('Items', []):
            user_id = item.get('userId')
            try:
                # Get user details from Cognito
                user_response = cognito.admin_get_user(
                    UserPoolId=user_pool_id,
                    Username=user_id
                )
                
                # Extract user attributes
                user_attributes = {}
                for attr in user_response.get('UserAttributes', []):
                    user_attributes[attr['Name']] = attr['Value']
                
                users.append({
                    'userId': user_id,
                    'email': user_attributes.get('email'),
                    'name': user_attributes.get('name'),
                    'role': item.get('role', 'user')  # Role in the company
                })
            except Exception as e:
                logger.error(f"Error getting user {user_id}: {str(e)}")
        
        return create_success_response({
            'companyId': company_id,
            'users': users
        })
    else:
        # If no specific query parameters, return the companies for the authenticated user
        response = user_company_table.query(
            KeyConditionExpression=Key('userId').eq(authenticated_user_id)
        )
        
        # Get company details for each company ID
        companies = []
        for item in response.get('Items', []):
            company_id = item.get('companyId')
            company_response = company_table.get_item(
                Key={'companyId': company_id}
            )
            company = company_response.get('Item')
            if company:
                companies.append(company)
        
        return create_success_response({
            'userId': authenticated_user_id,
            'companies': companies
        })

def handle_post_request(event, claims, is_admin):
    """
    Handle POST requests to create user-company relationships
    
    Request body:
    {
        "userId": "user-id",
        "companyId": "company-id",
        "role": "user|admin"  # Role within the company
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters
        user_id = body.get('userId')
        company_id = body.get('companyId')
        role = body.get('role', 'user')
        
        if not user_id or not company_id:
            return create_error_response(400, 'Bad Request', 'Missing required parameters: userId and companyId')
        
        # Check permissions: Only admins can assign users to companies
        if not is_admin:
            return create_error_response(403, 'Forbidden', 'Only admins can assign users to companies')
        
        # Verify the company exists
        company_response = company_table.get_item(
            Key={'companyId': company_id}
        )
        
        if not company_response.get('Item'):
            return create_error_response(404, 'Not Found', f'Company with ID {company_id} not found')
        
        # Verify the user exists in Cognito
        try:
            cognito.admin_get_user(
                UserPoolId=user_pool_id,
                Username=user_id
            )
        except Exception as e:
            logger.error(f"Error verifying user: {str(e)}")
            return create_error_response(404, 'Not Found', f'User with ID {user_id} not found')
        
        # Create the user-company relationship
        timestamp = datetime.datetime.now().isoformat()
        user_company_table.put_item(
            Item={
                'userId': user_id,
                'companyId': company_id,
                'role': role,
                'createdBy': claims.get('sub'),
                'createdAt': timestamp,
                'updatedAt': timestamp
            }
        )
        
        return create_success_response({
            'message': f'User {user_id} assigned to company {company_id} with role {role}',
            'userId': user_id,
            'companyId': company_id,
            'role': role
        })
        
    except json.JSONDecodeError:
        return create_error_response(400, 'Bad Request', 'Invalid JSON in request body')

def handle_delete_request(event, claims, is_admin):
    """
    Handle DELETE requests to remove user-company relationships
    
    Query parameters:
    - userId: User to remove
    - companyId: Company to remove the user from
    """
    query_params = event.get('queryStringParameters', {}) or {}
    
    # Extract parameters
    user_id = query_params.get('userId')
    company_id = query_params.get('companyId')
    
    if not user_id or not company_id:
        return create_error_response(400, 'Bad Request', 'Missing required parameters: userId and companyId')
    
    # Check permissions: Only admins can remove users from companies
    if not is_admin:
        return create_error_response(403, 'Forbidden', 'Only admins can remove users from companies')
    
    # Remove the user-company relationship
    user_company_table.delete_item(
        Key={
            'userId': user_id,
            'companyId': company_id
        }
    )
    
    return create_success_response({
        'message': f'User {user_id} removed from company {company_id}',
        'userId': user_id,
        'companyId': company_id
    })

def is_admin_user(claims):
    """
    Check if the user has admin privileges
    This is a simple implementation - you might want to use Cognito groups
    or a more sophisticated approach in a production environment
    """
    # You could check for a specific role claim or group membership
    # For now, we'll use a simple approach with a custom claim
    return claims.get('cognito:groups') and 'admin' in claims.get('cognito:groups')

def user_belongs_to_company(user_id, company_id):
    """Check if a user belongs to a company"""
    response = user_company_table.get_item(
        Key={
            'userId': user_id,
            'companyId': company_id
        }
    )
    
    return 'Item' in response

def create_success_response(data):
    """Create a standardized success response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,DELETE'
        },
        'body': json.dumps(data, cls=DecimalEncoder)
    }

def create_error_response(status_code, error, message):
    """Create a standardized error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST,DELETE'
        },
        'body': json.dumps({
            'error': error,
            'message': message
        }, cls=DecimalEncoder)
    }
