import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/config.dart';
import 'auth_service.dart';

class ApiService {
  final AuthService _authService = AuthService();
  
  // Singleton pattern
  static final ApiService _instance = ApiService._internal();
  
  factory ApiService() {
    return _instance;
  }
  
  ApiService._internal();
  
  // Helper method to get headers with authorization token
  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getIdToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ${token ?? ''}', // API Gateway with Cognito authorizer expects Bearer token
    };
  }
  
  // Get telemetry data for a specific device with optional time range
  Future<Map<String, dynamic>> getTelemetryData(String deviceId, {String? startTime, String? endTime}) async {
    try {
      // Build query parameters
      final queryParams = <String, String>{
        'deviceId': deviceId,
      };
      
      if (startTime != null) {
        queryParams['startTime'] = startTime;
      }
      
      if (endTime != null) {
        queryParams['endTime'] = endTime;
      }
      
      // Build URI with query parameters
      final uri = Uri.parse('${Config.apiUrl}/telemetry').replace(queryParameters: queryParams);
      
      // Make API request with authorization header
      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get telemetry data: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting telemetry data: $e');
    }
  }
  
  // Get all devices for a company
  Future<Map<String, dynamic>> getAllDevices(String companyId) async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/devices').replace(
        queryParameters: {'companyId': companyId},
      );
      
      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get devices: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting devices: $e');
    }
  }
  
  // Get user companies
  Future<Map<String, dynamic>> getUserCompanies() async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/user-company');
      print('API URL: ${Config.apiUrl}');
      print('Requesting companies from: $uri');
      
      final headers = await _getHeaders();
      print('Request headers: $headers');
      
      final response = await http.get(
        uri,
        headers: headers,
      );
      
      print('Response status: ${response.statusCode}');
      print('Response body: ${response.body}');
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get user companies: ${response.statusCode} - ${response.body}');
      }
    } catch (e) {
      print('Error getting user companies: $e');
      throw Exception('Error getting user companies: $e');
    }
  }
}
