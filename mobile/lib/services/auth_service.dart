import 'dart:async';
import 'package:amazon_cognito_identity_dart_2/cognito.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/config.dart';

class AuthService {
  late final CognitoUserPool _userPool;
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  CognitoUser? _cognitoUser;
  CognitoUserSession? _session;
  
  static final AuthService _instance = AuthService._internal();
  
  factory AuthService() {
    return _instance;
  }
  
  AuthService._internal() {
    _initUserPool();
  }
  
  void _initUserPool() {
    try {
      final userPoolId = Config.userPoolId;
      final clientId = Config.clientId;
      
      print('Initializing Cognito User Pool with:');
      print('User Pool ID: $userPoolId');
      
      _userPool = CognitoUserPool(
        userPoolId,
        clientId,
      );
    } catch (e) {
      print('Error initializing Cognito User Pool: $e');
      rethrow;
    }
  }
  
  // Sign in a user
  Future<bool> signIn(String email, String password) async {
    _cognitoUser = CognitoUser(
      email,
      _userPool,
      storage: CognitoMemoryStorage(),
    );
    
    final authDetails = AuthenticationDetails(
      username: email,
      password: password,
    );
    
    try {
      _session = await _cognitoUser!.authenticateUser(authDetails);
      
      // Store tokens securely
      await _secureStorage.write(
        key: 'idToken',
        value: _session!.getIdToken().getJwtToken(),
      );
      await _secureStorage.write(
        key: 'accessToken',
        value: _session!.getAccessToken().getJwtToken(),
      );
      await _secureStorage.write(
        key: 'refreshToken',
        value: _session!.getRefreshToken()?.getToken(),
      );
      await _secureStorage.write(key: 'email', value: email);
      
      return true;
    } catch (e) {
      print('Sign in error: $e');
      return false;
    }
  }
  
  // Sign out the current user
  Future<void> signOut() async {
    _cognitoUser?.signOut();
    await _secureStorage.deleteAll();
    _session = null;
  }
  
  // Check if user is authenticated
  Future<bool> isAuthenticated() async {
    try {
      final idToken = await _secureStorage.read(key: 'idToken');
      final accessToken = await _secureStorage.read(key: 'accessToken');
      final refreshToken = await _secureStorage.read(key: 'refreshToken');
      final email = await _secureStorage.read(key: 'email');
      
      if (idToken == null || accessToken == null || refreshToken == null || email == null) {
        return false;
      }
      
      // Initialize user
      _cognitoUser = CognitoUser(
        email,
        _userPool,
        storage: CognitoMemoryStorage(),
      );
      
      // Create session from tokens
      _session = CognitoUserSession(
        CognitoIdToken(idToken),
        CognitoAccessToken(accessToken),
        refreshToken: CognitoRefreshToken(refreshToken),
      );
      
      // Check if session is valid
      if (!_session!.isValid()) {
        // Try to refresh the session
        try {
          _session = await _cognitoUser!.refreshSession(CognitoRefreshToken(refreshToken));
          
          // Update stored tokens
          await _secureStorage.write(
            key: 'idToken',
            value: _session!.getIdToken().getJwtToken(),
          );
          await _secureStorage.write(
            key: 'accessToken',
            value: _session!.getAccessToken().getJwtToken(),
          );
          await _secureStorage.write(
            key: 'refreshToken',
            value: _session!.getRefreshToken()?.getToken(),
          );
          
          return true;
        } catch (e) {
          print('Session refresh error: $e');
          await signOut();
          return false;
        }
      }
      
      return true;
    } catch (e) {
      print('Authentication check error: $e');
      return false;
    }
  }
  
  // Get the current user's ID token
  Future<String?> getIdToken() async {
    if (await isAuthenticated()) {
      return _session?.getIdToken().getJwtToken();
    }
    return null;
  }
  
  // Get the current user's email
  Future<String?> getCurrentUserEmail() async {
    return await _secureStorage.read(key: 'email');
  }
}
