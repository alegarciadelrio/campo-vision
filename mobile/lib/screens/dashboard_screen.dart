import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../context/auth_context.dart';
import '../context/theme_context.dart';
import '../providers/dashboard_provider.dart';
import 'settings_screen.dart';
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
          // Company selector in app bar
          Consumer<DashboardProvider>(
            builder: (context, dashboardProvider, _) {
              if (dashboardProvider.isLoading || dashboardProvider.companies.isEmpty) {
                return const SizedBox(width: 40);
              }
              
              return DropdownButton<String>(
                value: dashboardProvider.selectedCompany?.companyId,
                hint: const Text('Select company', style: TextStyle(color: Colors.white70)),
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                underline: Container(height: 0),
                dropdownColor: Theme.of(context).colorScheme.primary,
                onChanged: (String? companyId) {
                  if (companyId != null) {
                    final company = dashboardProvider.companies.firstWhere(
                      (c) => c.companyId == companyId,
                    );
                    dashboardProvider.selectCompany(company);
                  }
                },
                items: dashboardProvider.companies.map((company) {
                  return DropdownMenuItem<String>(
                    value: company.companyId,
                    child: Text(company.name),
                  );
                }).toList(),
              );
            },
          ),
          
          // Settings button
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const SettingsScreen()),
            ),
            tooltip: 'Settings',
          ),
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
                              // Device map (full screen)
                              const Expanded(
                                child: DeviceMap(),
                              ),
                            ],
                          );
                        } else {
                          // Landscape: Map on full screen
                          return const DeviceMap();
                        }
                      },
                    ),
              ),
              
              // Collapsible devices section at the bottom
              const CollapsibleDevicesSection(),
            ],
          );
        },
      ),
    );
  }
}

/// A collapsible section that displays the device list at the bottom of the dashboard
class CollapsibleDevicesSection extends StatefulWidget {
  const CollapsibleDevicesSection({super.key});

  @override
  State<CollapsibleDevicesSection> createState() => _CollapsibleDevicesSectionState();
}

class _CollapsibleDevicesSectionState extends State<CollapsibleDevicesSection> with SingleTickerProviderStateMixin {
  bool _isExpanded = false;
  late AnimationController _controller;
  late Animation<double> _heightFactor;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _heightFactor = _controller.drive(CurveTween(curve: Curves.easeInOut));
  }
  
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
  
  void _toggleExpanded() {
    setState(() {
      _isExpanded = !_isExpanded;
      if (_isExpanded) {
        _controller.forward();
      } else {
        _controller.reverse();
      }
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Header bar with toggle button
        InkWell(
          onTap: _toggleExpanded,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primary,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 4.0,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Devices',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                Icon(
                  _isExpanded ? Icons.keyboard_arrow_down : Icons.keyboard_arrow_up,
                  color: Colors.white,
                ),
              ],
            ),
          ),
        ),
        
        // Expandable content
        AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            return ClipRect(
              child: Align(
                heightFactor: _heightFactor.value,
                child: child,
              ),
            );
          },
          child: Container(
            height: 300, // Fixed height for the device list when expanded
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4.0,
                  offset: const Offset(0, -1),
                ),
              ],
            ),
            child: const DeviceList(),
          ),
        ),
      ],
    );
  }
}
