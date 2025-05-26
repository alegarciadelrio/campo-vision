// Replace these values with your actual AWS resources when deploying
const config = {
  // API Gateway endpoint - will be populated from CloudFormation outputs
  apiUrl: process.env.REACT_APP_API_URL || 'https://your-api-id.execute-api.your-region.amazonaws.com/Prod',
  
  // Cognito configuration - will be populated from CloudFormation outputs
  cognito: {
    region: process.env.REACT_APP_REGION || 'your-region',
    userPoolId: process.env.REACT_APP_USER_POOL_ID || 'your-user-pool-id',
    userPoolWebClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID || 'your-app-client-id'
  }
};

export default config;
