# Campo Vision Frontend

This is the frontend application for Campo Vision, a telemetry system for agricultural equipment.

## Features

- Interactive map display of device positions using Mapbox GL
- Real-time telemetry data visualization
- Secure authentication with Amazon Cognito
- Filtering by device ID and time range
- Responsive design for desktop and mobile

## Setup and Development

### Prerequisites

- Node.js and npm
- AWS CLI configured with appropriate permissions
- An AWS account with access to S3, CloudFront, and Cognito
- Mapbox account and access token

### Local Development

1. Install dependencies:
   ```
   npm install
   ```

2. Create a `.env.local` file with your configuration:
   ```
   REACT_APP_API_URL=https://your-api-id.execute-api.your-region.amazonaws.com/Prod
   REACT_APP_REGION=your-region
   REACT_APP_USER_POOL_ID=your-user-pool-id
   REACT_APP_USER_POOL_CLIENT_ID=your-app-client-id
   REACT_APP_MAPBOX_TOKEN=your-mapbox-access-token
   ```

3. Start the development server:
   ```
   npm start
   ```

## Deployment to S3 and CloudFront

The frontend is designed to be deployed to AWS S3 and CloudFront using the CloudFormation template in the main project. The deployment process is automated through the `deploy-s3.sh` script. Run:

```NODE_ENV=production ./deploy-s3.sh```

To deploy manually:

1. Build the application:
   ```
   npm run build
   ```

2. Deploy to S3:
   ```
   S3_BUCKET=your-bucket-name CLOUDFRONT_DISTRIBUTION_ID=your-distribution-id npm run deploy
   ```

## Authentication

This application uses Amazon Cognito for authentication. It connects to the same Cognito User Pool that is used by the backend API.

## Map Integration

The application uses Mapbox GL JS for map visualization. You need to provide a Mapbox access token in the configuration.
