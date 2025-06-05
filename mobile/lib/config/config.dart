import 'package:flutter_dotenv/flutter_dotenv.dart';

// Configuration for Campo Vision Mobile App
class Config {
  // AWS Cognito configuration
  static String get region => dotenv.env['COGNITO_REGION'] ?? 'your-region';
  static String get userPoolId => dotenv.env['USER_POOL_ID'] ?? 'your-user-pool-id';
  static String get clientId => dotenv.env['USER_POOL_CLIENT_ID'] ?? 'your-app-client-id';
      
  // API configuration
  static String get apiUrl => dotenv.env['API_URL'] ?? 
      'https://your-api-id.execute-api.your-region.amazonaws.com/Prod';
}
