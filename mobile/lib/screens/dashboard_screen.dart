import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../context/auth_context.dart';
import '../context/theme_context.dart';
import '../providers/dashboard_provider.dart';
import '../widgets/company_selector.dart';
import '../widgets/device_list.dart';
import '../widgets/device_map.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    // Initialize dashboard data after the widget is built
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final dashboardProvider = Provider.of<DashboardProvider>(context, listen: false);
      dashboardProvider.initialize();
    });
  }

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
      body: Consumer<DashboardProvider>(
        builder: (context, dashboardProvider, _) {
          if (!dashboardProvider.hasCompanies && !dashboardProvider.isLoading) {
            // Show message if no companies are available
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.business, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text(
                    'No companies available',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Logged in as: ${authContext.userEmail ?? "Unknown User"}',
                    style: const TextStyle(fontSize: 16),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: () => dashboardProvider.fetchUserCompanies(),
                    child: const Text('Refresh'),
                  ),
                ],
              ),
            );
          }
          
          return Column(
            children: [
              // Company selector
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  children: [
                    const Text(
                      'Company:',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(width: 8),
                    Expanded(child: CompanySelector()),
                  ],
                ),
              ),
              
              // Main content - Device list and map
              Expanded(
                child: dashboardProvider.isLoading && dashboardProvider.devices.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 16),
                          Text('Loading dashboard data...'),
                        ],
                      ),
                    )
                  : OrientationBuilder(
                      builder: (context, orientation) {
                        // Use different layouts for portrait and landscape
                        if (orientation == Orientation.portrait) {
                          // Portrait: List on top, map on bottom
                          return Column(
                            children: [
                              // Device list (1/3 of screen)
                              Expanded(
                                flex: 1,
                                child: DeviceList(),
                              ),
                              // Device map (2/3 of screen)
                              Expanded(
                                flex: 2,
                                child: DeviceMap(),
                              ),
                            ],
                          );
                        } else {
                          // Landscape: List on left, map on right
                          return Row(
                            children: [
                              // Device list (1/3 of screen)
                              Expanded(
                                flex: 1,
                                child: DeviceList(),
                              ),
                              // Device map (2/3 of screen)
                              Expanded(
                                flex: 2,
                                child: DeviceMap(),
                              ),
                            ],
                          );
                        }
                      },
                    ),
              ),
            ],
          );
        },
      ),
    );
  }
}
