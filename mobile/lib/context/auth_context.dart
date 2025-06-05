import 'package:flutter/material.dart';
import '../services/auth_service.dart';

class AuthContext extends ChangeNotifier {
  final AuthService _authService = AuthService();
  bool _isAuthenticated = false;
  bool _isLoading = true;
  String? _userEmail;

  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get userEmail => _userEmail;

  AuthContext() {
    checkAuthStatus();
  }

  // Check if the user is authenticated
  Future<void> checkAuthStatus() async {
    _isLoading = true;
    notifyListeners();

    try {
      _isAuthenticated = await _authService.isAuthenticated();
      if (_isAuthenticated) {
        _userEmail = await _authService.getCurrentUserEmail();
      } else {
        _userEmail = null;
      }
    } catch (e) {
      _isAuthenticated = false;
      _userEmail = null;
      print('Error checking auth status: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Sign in a user
  Future<bool> signIn(String email, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final success = await _authService.signIn(email, password);
      if (success) {
        _isAuthenticated = true;
        _userEmail = email;
      }
      return success;
    } catch (e) {
      print('Sign in error: $e');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Sign out the current user
  Future<void> signOut() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _authService.signOut();
      _isAuthenticated = false;
      _userEmail = null;
    } catch (e) {
      print('Sign out error: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Get the current user's ID token for API calls
  Future<String?> getIdToken() async {
    return await _authService.getIdToken();
  }
}
