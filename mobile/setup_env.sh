#!/bin/bash

# Campo Vision Mobile App Environment Setup Script

echo "Setting up environment for Campo Vision Mobile App..."

# Check if .env file exists
if [ -f .env ]; then
  echo "Found existing .env file."
else
  echo "Creating new .env file from template..."
  cp .env.example .env
  
  # Prompt for configuration values
  read -p "Enter Cognito Region (e.g., us-east-1): " region
  read -p "Enter User Pool ID: " user_pool_id
  read -p "Enter User Pool Client ID: " client_id
  read -p "Enter API URL: " api_url
  
  # Update .env file with provided values
  if [ ! -z "$region" ]; then
    sed -i "s/COGNITO_REGION=.*/COGNITO_REGION=$region/" .env
  fi
  
  if [ ! -z "$user_pool_id" ]; then
    sed -i "s/USER_POOL_ID=.*/USER_POOL_ID=$user_pool_id/" .env
  fi
  
  if [ ! -z "$client_id" ]; then
    sed -i "s/USER_POOL_CLIENT_ID=.*/USER_POOL_CLIENT_ID=$client_id/" .env
  fi
  
  if [ ! -z "$api_url" ]; then
    sed -i "s|API_URL=.*|API_URL=$api_url|" .env
  fi
fi

echo "Installing dependencies..."
flutter pub get

echo "Environment setup complete!"
echo "You can now run the app with: flutter run"
