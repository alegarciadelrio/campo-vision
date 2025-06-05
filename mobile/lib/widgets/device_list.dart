import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/device.dart';
import '../providers/dashboard_provider.dart';

class DeviceList extends StatefulWidget {
  const DeviceList({Key? key}) : super(key: key);

  @override
  State<DeviceList> createState() => _DeviceListState();
}

class _DeviceListState extends State<DeviceList> {
  String _searchTerm = '';
  
  @override
  Widget build(BuildContext context) {
    return Consumer<DashboardProvider>(
      builder: (context, dashboardProvider, _) {
        // Filter devices based on search term
        final filteredDevices = dashboardProvider.devices
            .where((device) => 
                (device.name?.toLowerCase().contains(_searchTerm.toLowerCase()) ?? false) ||
                device.deviceId.toLowerCase().contains(_searchTerm.toLowerCase()) ||
                (device.description?.toLowerCase().contains(_searchTerm.toLowerCase()) ?? false))
            .toList();
        
        return Card(
          margin: const EdgeInsets.all(8.0),
          elevation: 4,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header with title and refresh button
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Devices',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    IconButton(
                      icon: dashboardProvider.isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.refresh),
                      onPressed: dashboardProvider.isLoading
                          ? null
                          : () {
                              if (dashboardProvider.selectedCompany != null) {
                                dashboardProvider.fetchDevices(
                                    dashboardProvider.selectedCompany!.companyId);
                              }
                            },
                      tooltip: 'Refresh',
                    ),
                  ],
                ),
              ),
              
              // Search box
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8.0),
                child: TextField(
                  decoration: const InputDecoration(
                    hintText: 'Search devices...',
                    prefixIcon: Icon(Icons.search),
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(vertical: 8.0),
                  ),
                  onChanged: (value) {
                    setState(() {
                      _searchTerm = value;
                    });
                  },
                ),
              ),
              
              // Error message if any
              if (dashboardProvider.error != null)
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Container(
                    padding: const EdgeInsets.all(8.0),
                    color: Colors.red[100],
                    child: Text(
                      dashboardProvider.error!,
                      style: TextStyle(color: Colors.red[900]),
                    ),
                  ),
                ),
              
              // Device list
              Expanded(
                child: _buildDeviceListContent(dashboardProvider, filteredDevices),
              ),
            ],
          ),
        );
      },
    );
  }
  
  Widget _buildDeviceListContent(DashboardProvider provider, List<Device> filteredDevices) {
    if (provider.isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading devices...'),
          ],
        ),
      );
    }
    
    if (provider.selectedCompany == null) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text(
            'Please select a company from the dropdown to view devices',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }
    
    if (filteredDevices.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text(
            'No devices found for the selected company',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }
    
    return ListView.builder(
      itemCount: filteredDevices.length,
      itemBuilder: (context, index) {
        final device = filteredDevices[index];
        final isSelected = provider.selectedDevice?.deviceId == device.deviceId;
        final hasLocation = device.hasLocation();
        
        return ListTile(
          title: Text(
            device.name ?? device.deviceId,
            style: TextStyle(
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          subtitle: device.description != null
              ? Text(device.description!)
              : null,
          leading: Icon(
            Icons.circle,
            color: hasLocation ? Colors.green : Colors.grey,
            size: 12,
          ),
          trailing: Text(
            hasLocation
                ? _formatDate(device.lastTelemetry!.timestamp)
                : 'No data',
            style: TextStyle(
              color: hasLocation ? Colors.black54 : Colors.grey,
              fontSize: 12,
            ),
          ),
          selected: isSelected,
          selectedTileColor: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
          onTap: () => provider.selectDevice(device),
        );
      },
    );
  }
  
  String _formatDate(String timestamp) {
    final date = DateTime.parse(timestamp);
    return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }
}
