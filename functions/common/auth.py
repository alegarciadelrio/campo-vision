import json
import os
import time
import urllib.request
from jose import jwk, jwt
from jose.utils import base64url_decode
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global variables
cognito_user_pool_id = None
cognito_region = None
keys = None
claims = None

def get_public_keys():
    """Retrieves the public keys from Cognito User Pool"""
    global keys
    if keys:
        return keys
    
    region = get_cognito_region()
    user_pool_id = get_cognito_user_pool_id()
    
    keys_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
    
    try:
        with urllib.request.urlopen(keys_url) as f:
            response = f.read()
        keys = json.loads(response.decode('utf-8'))['keys']
        return keys
    except Exception as e:
        logger.error(f"Error retrieving public keys: {str(e)}")
        return None

def get_cognito_user_pool_id():
    """Gets the Cognito User Pool ID from environment variables"""
    global cognito_user_pool_id
    if cognito_user_pool_id:
        return cognito_user_pool_id
    
    cognito_user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
    return cognito_user_pool_id

def get_cognito_region():
    """Gets the Cognito region from environment variables or defaults to the Lambda region"""
    global cognito_region
    if cognito_region:
        return cognito_region
    
    cognito_region = os.environ.get('COGNITO_REGION', os.environ.get('AWS_REGION', 'us-east-1'))
    return cognito_region

def verify_token(token):
    """Verifies the JWT token from Cognito"""
    global claims
    
    # If we've already verified this token, return the cached claims
    if claims:
        return claims
    
    # Get the kid (key ID) from the token headers
    try:
        headers = jwt.get_unverified_headers(token)
        kid = headers['kid']
    except Exception as e:
        logger.error(f"Error getting token headers: {str(e)}")
        return None
    
    # Get the public keys
    keys = get_public_keys()
    if not keys:
        return None
    
    # Find the key that matches the kid in the token
    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    
    if key_index == -1:
        logger.error("Public key not found in jwks.json")
        return None
    
    # Get the public key
    public_key = jwk.construct(keys[key_index])
    
    # Get the message and signature from the token
    message, encoded_signature = token.rsplit('.', 1)
    decoded_signature = base64url_decode(encoded_signature.encode('utf-8'))
    
    # Verify the signature
    if not public_key.verify(message.encode('utf-8'), decoded_signature):
        logger.error("Signature verification failed")
        return None
    
    # Verify the claims
    try:
        claims = jwt.get_unverified_claims(token)
        
        # Verify expiration time
        if time.time() > claims['exp']:
            logger.error("Token is expired")
            return None
        
        # Verify audience (client ID)
        # Note: This check is optional and depends on your security requirements
        # token_use = claims.get('token_use')
        # if token_use != 'access':
        #     logger.error(f"Token use is not 'access', got: {token_use}")
        #     return None
        
        # Verify issuer
        issuer = f'https://cognito-idp.{get_cognito_region()}.amazonaws.com/{get_cognito_user_pool_id()}'
        if claims['iss'] != issuer:
            logger.error(f"Invalid issuer: {claims['iss']}, expected: {issuer}")
            return None
        
        # Token is valid, return the claims
        return claims
    
    except Exception as e:
        logger.error(f"Error verifying token claims: {str(e)}")
        return None

def extract_token_from_header(event):
    """Extracts the JWT token from the Authorization header"""
    try:
        auth_header = event.get('headers', {}).get('Authorization')
        if not auth_header:
            auth_header = event.get('headers', {}).get('authorization')
        
        if not auth_header:
            logger.error("No Authorization header found")
            return None
        
        # Check if it's a Bearer token
        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            logger.error("Authorization header is not a Bearer token")
            return None
        
        token = parts[1]
        return token
    
    except Exception as e:
        logger.error(f"Error extracting token from header: {str(e)}")
        return None

def get_user_from_event(event):
    """Gets the authenticated user from the event"""
    token = extract_token_from_header(event)
    if not token:
        return None
    
    claims = verify_token(token)
    if not claims:
        return None
    
    # Return user information from the claims
    return {
        'user_id': claims.get('sub'),
        'email': claims.get('email'),
        'username': claims.get('cognito:username'),
        'groups': claims.get('cognito:groups', [])
    }

def require_auth(event):
    """Requires authentication for the request"""
    user = get_user_from_event(event)
    if not user:
        return {
            'statusCode': 401,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Unauthorized',
                'message': 'Authentication required'
            })
        }
    
    return None  # Authentication successful
