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
  
  // Get a specific device by ID
  Future<Map<String, dynamic>> getDeviceById(String deviceId) async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/device').replace(
        queryParameters: {'deviceId': deviceId},
      );
      
      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get device: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting device: $e');
    }
  }
  
  // Register a new device
  Future<Map<String, dynamic>> registerDevice(Map<String, dynamic> deviceData) async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/devices');
      
      final response = await http.post(
        uri,
        headers: await _getHeaders(),
        body: json.encode(deviceData),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to register device: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error registering device: $e');
    }
  }
  
  // Update an existing device
  Future<Map<String, dynamic>> updateDevice(String deviceId, Map<String, dynamic> deviceData) async {
    try {
      // Following the web app's approach: delete and recreate the device
      
      // Step 1: Delete the existing device
      try {
        await deleteDevice(deviceId);
      } catch (e) {
        // Ignore delete errors, we'll try to recreate anyway
        print('Error deleting device during update: $e');
      }
      
      // Step 2: Create a new device with the same ID but updated fields
      final completeDevice = {
        'deviceId': deviceId,
        'name': deviceData['name'] ?? '',
        'description': deviceData['description'] ?? '',
      };
      
      if (deviceData.containsKey('companyId')) {
        completeDevice['companyId'] = deviceData['companyId'];
      }
      
      await registerDevice(completeDevice);
      
      return {'success': true};
    } catch (e) {
      print('Device update failed: $e');
      return {'success': false, 'error': e.toString()};
    }
  }
  
  // Delete a device
  Future<Map<String, dynamic>> deleteDevice(String deviceId) async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/devices').replace(
        queryParameters: {'deviceId': deviceId},
      );
      
      final response = await http.delete(
        uri,
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to delete device: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error deleting device: $e');
    }
  }
  
  // Get a specific company by ID
  Future<Map<String, dynamic>> getCompanyById(String companyId) async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/company').replace(
        queryParameters: {'companyId': companyId},
      );
      
      final response = await http.get(
        uri,
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get company: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting company: $e');
    }
  }
  
  // Register a new company
  Future<Map<String, dynamic>> registerCompany(Map<String, dynamic> companyData) async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/company');
      
      final response = await http.post(
        uri,
        headers: await _getHeaders(),
        body: json.encode(companyData),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to register company: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error registering company: $e');
    }
  }
  
  // Update an existing company
  Future<Map<String, dynamic>> updateCompany(String companyId, Map<String, dynamic> companyData) async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/company');
      
      // Make sure we're only sending the fields the backend expects
      final payload = {
        'companyId': companyId,
        'name': companyData['name'] ?? '',
        'description': companyData['description'] ?? '',
      };
      
      final response = await http.put(
        uri,
        headers: await _getHeaders(),
        body: json.encode(payload),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to update company: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error updating company: $e');
    }
  }
  
  // Delete a company
  Future<Map<String, dynamic>> deleteCompany(String companyId) async {
    try {
      final uri = Uri.parse('${Config.apiUrl}/company').replace(
        queryParameters: {'companyId': companyId},
      );
      
      final response = await http.delete(
        uri,
        headers: await _getHeaders(),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to delete company: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error deleting company: $e');
    }
  }
}
