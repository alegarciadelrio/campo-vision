#!/bin/bash

# Check if we're in development mode
if [ "$NODE_ENV" != "production" ]; then
  echo "Running in development mode..."
  npm start
  exit 0
fi

# For production deployment
# Load environment variables from .env.production
if [ -f .env.production ]; then
  echo "Loading environment variables from .env.production..."
  export $(grep -v '^#' .env.production | xargs)
fi

# Configuration - use environment variables with fallbacks
S3_BUCKET=${S3_BUCKET:-"$(aws cloudformation describe-stacks --stack-name campo-vision --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue" --output text)"}
CLOUDFRONT_DISTRIBUTION_ID=${CLOUDFRONT_DISTRIBUTION_ID:-"$(aws cloudformation describe-stacks --stack-name campo-vision --query "Stacks[0].Outputs[?OutputKey=='FrontendCloudFrontDistributionId'].OutputValue" --output text)"}
REGION=${AWS_REGION:-"us-east-1"}

# Build the React app
echo "Building React application..."
npm run build

# Check if build directory exists
if [ ! -d "build" ]; then
  echo "Error: build directory does not exist. Build failed."
  exit 1
fi

# Check if S3 bucket exists
aws s3 ls s3://$S3_BUCKET > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Error: S3 bucket $S3_BUCKET does not exist or you don't have access to it."
  echo "Please deploy the CloudFormation stack first or specify a valid bucket."
  exit 1
fi

# Upload to S3
echo "Uploading to S3 bucket: $S3_BUCKET"
aws s3 sync build/ s3://$S3_BUCKET --delete --region $REGION

# Invalidate CloudFront cache if distribution ID is provided
if [ "$CLOUDFRONT_DISTRIBUTION_ID" != "your-cloudfront-distribution-id" ]; then
  echo "Invalidating CloudFront cache..."
  aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*" --region $REGION
else
  echo "Skipping CloudFront invalidation - no distribution ID provided."
fi

echo "Deployment complete!"
