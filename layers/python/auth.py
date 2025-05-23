import os
import json
import logging
import base64
import urllib.request
from jose import jwk, jwt
from jose.utils import base64url_decode

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
USER_POOL_ID = os.environ.get('USER_POOL_ID')
USER_POOL_CLIENT_ID = os.environ.get('USER_POOL_CLIENT_ID')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# JWT token validation
def validate_token(token):
    """
    Validates a JWT token from AWS Cognito
    
    Args:
        token (str): The JWT token to validate
        
    Returns:
        dict: The claims from the token if valid
        
    Raises:
        Exception: If the token is invalid
    """
    try:
        # Get the key id from the token header
        token_sections = token.split('.')
        if len(token_sections) < 2:
            raise Exception('Token is invalid')
            
        header = json.loads(base64.b64decode(token_sections[0] + '==').decode('utf-8'))
        kid = header['kid']
        
        # Get the public keys from Cognito
        keys_url = f'https://cognito-idp.{AWS_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'
        with urllib.request.urlopen(keys_url) as f:
            response = f.read()
        keys = json.loads(response.decode('utf-8'))['keys']
        
        # Find the key matching the kid from the token
        key = None
        for k in keys:
            if k['kid'] == kid:
                key = k
                break
                
        if not key:
            raise Exception('Public key not found')
            
        # Get the public key
        public_key = jwk.construct(key)
        
        # Verify the signature
        message = token_sections[0].encode('utf-8') + '.'.encode('utf-8') + token_sections[1].encode('utf-8')
        signature = base64url_decode(token_sections[2].encode('utf-8'))
        
        if not public_key.verify(message, signature):
            raise Exception('Signature verification failed')
            
        # Verify the claims
        claims = jwt.get_unverified_claims(token)
        
        # Verify the token use (accept both access and id tokens)
        if claims['token_use'] not in ['access', 'id']:
            raise Exception('Token is not a valid token type')
            
        # Verify the client ID - handle different token structures
        # For ID tokens, the client_id might be in 'aud' field instead
        client_id = claims.get('client_id')
        if not client_id:
            # For ID tokens, check the 'aud' field
            client_id = claims.get('aud')
            
        if not client_id or (client_id != USER_POOL_CLIENT_ID):
            raise Exception('Token was not issued for this client')
            
        # Verify the expiration
        import time
        if time.time() > claims['exp']:
            raise Exception('Token has expired')
            
        return claims
        
    except Exception as e:
        logger.error(f'Token validation error: {str(e)}')
        raise Exception(f'Token validation error: {str(e)}')

def get_token_from_header(event):
    """
    Extracts the JWT token from the Authorization header
    
    Args:
        event (dict): The Lambda event
        
    Returns:
        str: The JWT token
        
    Raises:
        Exception: If the token is not found
    """
    try:
        auth_header = event['headers'].get('Authorization')
        if not auth_header:
            auth_header = event['headers'].get('authorization')
            
        if not auth_header:
            raise Exception('Authorization header is missing')
            
        token_parts = auth_header.split()
        if len(token_parts) != 2 or token_parts[0].lower() != 'bearer':
            raise Exception('Authorization header is malformed')
            
        return token_parts[1]
        
    except Exception as e:
        logger.error(f'Error extracting token: {str(e)}')
        raise Exception(f'Error extracting token: {str(e)}')

def require_auth(event):
    """
    Validates the JWT token in the request and returns the claims
    
    Args:
        event (dict): The Lambda event
        
    Returns:
        dict: The claims from the token if valid
        
    Raises:
        Exception: If the token is invalid
    """
    # Skip auth for OPTIONS requests (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return None
        
    token = get_token_from_header(event)
    return validate_token(token)
