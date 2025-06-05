import 'package:flutter_dotenv/flutter_dotenv.dart';

// Configuration for Campo Vision Mobile App
class Config {
  // Print environment variables for debugging
  static void printEnvVars() {
    print('Environment variables:');
    print('COGNITO_REGION: ${dotenv.env['COGNITO_REGION']}');
    print('USER_POOL_ID: ${dotenv.env['USER_POOL_ID']}');
    print('API_URL: ${dotenv.env['API_URL']}');
  }

  // AWS Cognito configuration
  static String get region => dotenv.env['COGNITO_REGION'] ?? 'your-region';
  static String get userPoolId => dotenv.env['USER_POOL_ID'] ?? 'your-user-pool-id';
  static String get clientId => dotenv.env['USER_POOL_CLIENT_ID'] ?? 'your-app-client-id';
      
  // API configuration
  static String get apiUrl => dotenv.env['API_URL'] ?? 
      'https://api.campo-vision.com/v1';
}
