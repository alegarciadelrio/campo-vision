import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:provider/provider.dart';
import 'config/config.dart';
import 'context/auth_context.dart';
import 'context/theme_context.dart';
import 'providers/dashboard_provider.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';

void main() async {
  // Ensure Flutter is initialized
  WidgetsFlutterBinding.ensureInitialized();
  
  // Load environment variables
  try {
    // Try loading with default path first
    await dotenv.load();
    print('Environment variables loaded successfully from default path');
  } catch (e) {
    print('Error loading .env from default path: $e');
    
    // Try with explicit path as fallback
    try {
      await dotenv.load(fileName: '.env');
      print('Environment variables loaded successfully with explicit path');
    } catch (e) {
      print('Error loading .env with explicit path: $e');
    }
  }
  
  // Debug environment variables
  if (dotenv.env.isNotEmpty) {
    print('Environment variables loaded:');
    print('COGNITO_REGION: ${dotenv.env['COGNITO_REGION']}');
    print('USER_POOL_ID: ${dotenv.env['USER_POOL_ID']}');
    print('API_URL: ${dotenv.env['API_URL']}');
    // Don't print client ID for security reasons
    Config.printEnvVars();
  } else {
    print('WARNING: No environment variables loaded!');
  }
  
  runApp(const CampoVisionApp());
}

class CampoVisionApp extends StatelessWidget {
  const CampoVisionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthContext()),
        ChangeNotifierProvider(create: (_) => ThemeContext()),
        ChangeNotifierProvider(create: (_) => DashboardProvider()),
      ],
      child: Consumer<ThemeContext>(
        builder: (context, themeContext, _) => MaterialApp(
        title: 'Campo Vision',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
          useMaterial3: true,
        ),
        darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.green,
            brightness: Brightness.dark,
          ),
          useMaterial3: true,
        ),
        themeMode: themeContext.themeMode,
        home: const AuthWrapper(),
      )),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    final authContext = Provider.of<AuthContext>(context);
    
    // Show loading indicator while checking authentication status
    if (authContext.isLoading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }
    
    // Navigate to appropriate screen based on authentication status
    return authContext.isAuthenticated 
        ? const DashboardScreen() 
        : const LoginScreen();
  }
}
