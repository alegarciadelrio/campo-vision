import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../context/auth_context.dart';
import '../context/theme_context.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authContext = Provider.of<AuthContext>(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Campo Vision'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
        actions: [
          // Theme toggle button
          Consumer<ThemeContext>(
            builder: (context, themeContext, _) => IconButton(
              icon: Icon(
                themeContext.isDarkMode ? Icons.light_mode : Icons.dark_mode,
              ),
              onPressed: () => themeContext.toggleTheme(),
              tooltip: themeContext.isDarkMode ? 'Light Mode' : 'Dark Mode',
            ),
          ),
          // Logout button
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => authContext.signOut(),
            tooltip: 'Sign Out',
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Welcome to Campo Vision',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Text(
              'Logged in as: ${authContext.userEmail ?? "Unknown User"}',
              style: const TextStyle(fontSize: 16),
            ),
          ],
        ),
      ),
    );
  }
}
