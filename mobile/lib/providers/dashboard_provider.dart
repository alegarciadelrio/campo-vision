import 'package:flutter/material.dart';
import '../models/device.dart';
import '../models/company.dart';
import '../services/api_service.dart';

class DashboardProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  // State variables
  List<Company> _companies = [];
  List<Device> _devices = [];
  Company? _selectedCompany;
  Device? _selectedDevice;
  bool _isLoading = false;
  String? _error;
  
  // Getters
  List<Company> get companies => _companies;
  List<Device> get devices => _devices;
  Company? get selectedCompany => _selectedCompany;
  Device? get selectedDevice => _selectedDevice;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasCompanies => _companies.isNotEmpty;
  
  // Filtered devices getter (devices with location data)
  List<Device> get devicesWithLocation => _devices.where((device) => device.hasLocation()).toList();
  
  // Initialize dashboard data
  Future<void> initialize() async {
    await fetchUserCompanies();
    if (_companies.isNotEmpty) {
      await selectCompany(_companies.first);
    }
  }
  
  // Fetch user companies
  Future<void> fetchUserCompanies() async {
    _setLoading(true);
    _error = null;
    
    try {
      print('Fetching user companies...');
      final response = await _apiService.getUserCompanies();
      print('API response: $response');
      
      if (response.containsKey('companies')) {
        _companies = (response['companies'] as List)
            .map((company) => Company.fromJson(company))
            .toList();
        
        print('Companies loaded: ${_companies.length}');
        notifyListeners();
      } else {
        print('Invalid response format: $response');
        _error = 'Invalid response format';
      }
    } catch (e) {
      _error = 'Failed to fetch companies: $e';
    } finally {
      _setLoading(false);
    }
  }
  
  // Fetch devices for a company
  Future<void> fetchDevices(String companyId) async {
    _setLoading(true);
    _error = null;
    _devices = [];
    
    try {
      final response = await _apiService.getAllDevices(companyId);
      
      if (response.containsKey('devices')) {
        _devices = (response['devices'] as List)
            .map((device) => Device.fromJson(device))
            .toList();
        
        notifyListeners();
      } else {
        _error = 'Invalid response format';
      }
    } catch (e) {
      _error = 'Failed to fetch devices: $e';
    } finally {
      _setLoading(false);
    }
  }
  
  // Select a company and fetch its devices
  Future<void> selectCompany(Company company) async {
    _selectedCompany = company;
    _selectedDevice = null;
    notifyListeners();
    
    await fetchDevices(company.companyId);
  }
  
  // Select a device
  void selectDevice(Device device) {
    _selectedDevice = device;
    notifyListeners();
  }
  
  // Fetch telemetry data for a device
  Future<List<Telemetry>> fetchDeviceTelemetry(String deviceId, {DateTime? startTime, DateTime? endTime}) async {
    try {
      final start = startTime?.toUtc().toIso8601String() ?? 
                   DateTime.now().subtract(const Duration(hours: 24)).toUtc().toIso8601String();
      final end = endTime?.toUtc().toIso8601String() ?? 
                 DateTime.now().toUtc().toIso8601String();
      
      final response = await _apiService.getTelemetryData(
        deviceId,
        startTime: start,
        endTime: end,
      );
      
      if (response.containsKey('telemetry')) {
        return (response['telemetry'] as List)
            .map((telemetry) => Telemetry.fromJson(telemetry))
            .toList();
      } else {
        return [];
      }
    } catch (e) {
      _error = 'Failed to fetch telemetry: $e';
      return [];
    }
  }
  
  // Helper to set loading state
  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }
  
  // Clear errors
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
