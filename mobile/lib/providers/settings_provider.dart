import 'package:flutter/material.dart';
import '../models/company.dart';
import '../models/device.dart';
import '../services/api_service.dart';

class SettingsProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  List<Company> _companies = [];
  List<Device> _devices = [];
  Company? _selectedCompany;
  bool _isLoading = false;
  String _error = '';

  // Getters
  List<Company> get companies => _companies;
  List<Device> get devices => _devices;
  Company? get selectedCompany => _selectedCompany;
  bool get isLoading => _isLoading;
  String get error => _error;
  bool get hasCompanies => _companies.isNotEmpty;
  bool get hasDevices => _devices.isNotEmpty;

  // Initialize the provider
  Future<void> initialize() async {
    await fetchCompanies();
  }

  // Fetch companies from API
  Future<void> fetchCompanies() async {
    _setLoading(true);
    try {
      final response = await _apiService.getUserCompanies();
      if (response.containsKey('companies')) {
        _companies = (response['companies'] as List)
            .map((company) => Company.fromJson(company))
            .toList();
        
        // Set first company as selected if available
        if (_companies.isNotEmpty) {
          _selectedCompany = _companies.first;
          await fetchDevices(_selectedCompany!.companyId);
        }
        _setError('');
      } else {
        _companies = [];
        _setError('Failed to load companies: Invalid response format');
      }
    } catch (e) {
      _companies = [];
      _setError('Failed to load companies: ${e.toString()}');
    } finally {
      _setLoading(false);
    }
  }

  // Fetch devices for a specific company
  Future<void> fetchDevices(String companyId) async {
    _setLoading(true);
    try {
      final response = await _apiService.getAllDevices(companyId);
      if (response.containsKey('devices')) {
        _devices = (response['devices'] as List)
            .map((device) => Device.fromJson(device))
            .toList();
        _setError('');
      } else {
        _devices = [];
        _setError('Failed to load devices: Invalid response format');
      }
    } catch (e) {
      _devices = [];
      _setError('Failed to load devices: ${e.toString()}');
    } finally {
      _setLoading(false);
    }
  }

  // Select a company
  void selectCompany(Company company) {
    _selectedCompany = company;
    fetchDevices(company.companyId);
    notifyListeners();
  }

  // Add a new company
  Future<bool> addCompany(String name, String description) async {
    _setLoading(true);
    try {
      await _apiService.registerCompany({
        'name': name,
        'description': description,
      });
      await fetchCompanies();
      _setError('');
      return true;
    } catch (e) {
      _setError('Failed to add company: ${e.toString()}');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Update an existing company
  Future<bool> updateCompany(String companyId, String name, String description) async {
    _setLoading(true);
    try {
      await _apiService.updateCompany(companyId, {
        'companyId': companyId,
        'name': name,
        'description': description,
      });
      await fetchCompanies();
      _setError('');
      return true;
    } catch (e) {
      _setError('Failed to update company: ${e.toString()}');
      // Try to refresh the list anyway
      await fetchCompanies();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Delete a company
  Future<bool> deleteCompany(String companyId) async {
    _setLoading(true);
    try {
      await _apiService.deleteCompany(companyId);
      await fetchCompanies();
      _setError('');
      return true;
    } catch (e) {
      _setError('Failed to delete company: ${e.toString()}');
      // Try to refresh the list anyway
      await fetchCompanies();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Add a new device
  Future<bool> addDevice(String deviceId, String name, String description, String companyId) async {
    _setLoading(true);
    try {
      await _apiService.registerDevice({
        'deviceId': deviceId,
        'name': name,
        'description': description,
        'companyId': companyId,
      });
      await fetchDevices(companyId);
      _setError('');
      return true;
    } catch (e) {
      _setError('Failed to add device: ${e.toString()}');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Update an existing device
  Future<bool> updateDevice(String deviceId, String name, String description, String companyId) async {
    _setLoading(true);
    try {
      await _apiService.updateDevice(deviceId, {
        'deviceId': deviceId,
        'name': name,
        'description': description,
        'companyId': companyId,
      });
      await fetchDevices(companyId);
      _setError('');
      return true;
    } catch (e) {
      _setError('Failed to update device: ${e.toString()}');
      // Try to refresh the list anyway
      await fetchDevices(companyId);
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Delete a device
  Future<bool> deleteDevice(String deviceId, String companyId) async {
    _setLoading(true);
    try {
      await _apiService.deleteDevice(deviceId);
      await fetchDevices(companyId);
      _setError('');
      return true;
    } catch (e) {
      _setError('Failed to delete device: ${e.toString()}');
      // Try to refresh the list anyway
      await fetchDevices(companyId);
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // Helper methods
  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _error = error;
    notifyListeners();
  }

  void clearError() {
    _error = '';
    notifyListeners();
  }
}
