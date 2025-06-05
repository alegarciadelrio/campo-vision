import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ThemeContext extends ChangeNotifier {
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  ThemeMode _themeMode = ThemeMode.system;
  
  ThemeMode get themeMode => _themeMode;
  
  ThemeContext() {
    _loadThemePreference();
  }
  
  Future<void> _loadThemePreference() async {
    try {
      final themePreference = await _secureStorage.read(key: 'theme_mode');
      if (themePreference != null) {
        _themeMode = _getThemeModeFromString(themePreference);
        notifyListeners();
      }
    } catch (e) {
      print('Error loading theme preference: $e');
    }
  }
  
  ThemeMode _getThemeModeFromString(String themeMode) {
    switch (themeMode) {
      case 'light':
        return ThemeMode.light;
      case 'dark':
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }
  
  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    notifyListeners();
    
    String themeModeString;
    switch (mode) {
      case ThemeMode.light:
        themeModeString = 'light';
        break;
      case ThemeMode.dark:
        themeModeString = 'dark';
        break;
      default:
        themeModeString = 'system';
    }
    
    try {
      await _secureStorage.write(key: 'theme_mode', value: themeModeString);
    } catch (e) {
      print('Error saving theme preference: $e');
    }
  }
  
  bool get isDarkMode {
    if (_themeMode == ThemeMode.system) {
      // Get system brightness (this will need to be updated when app is running)
      final window = WidgetsBinding.instance.platformDispatcher;
      return window.platformBrightness == Brightness.dark;
    }
    return _themeMode == ThemeMode.dark;
  }
  
  void toggleTheme() {
    setThemeMode(isDarkMode ? ThemeMode.light : ThemeMode.dark);
  }
}
