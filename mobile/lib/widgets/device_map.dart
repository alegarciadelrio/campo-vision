import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import '../models/device.dart';
import '../providers/dashboard_provider.dart';

class DeviceMap extends StatefulWidget {
  const DeviceMap({Key? key}) : super(key: key);

  @override
  State<DeviceMap> createState() => _DeviceMapState();
}

class _DeviceMapState extends State<DeviceMap> {
  final MapController _mapController = MapController();
  List<Telemetry> _deviceTelemetry = [];
  bool _showTrack = false;
  DateTime _startDate = DateTime.now().subtract(const Duration(hours: 24));
  DateTime _endDate = DateTime.now();
  
  @override
  Widget build(BuildContext context) {
    return Consumer<DashboardProvider>(
      builder: (context, dashboardProvider, _) {
        // Default map center (Chile)
        LatLng mapCenter = const LatLng(-33.4, -70.9);
        double mapZoom = 5.0;
        
        // If a device is selected and has location, center on it
        if (dashboardProvider.selectedDevice != null && 
            dashboardProvider.selectedDevice!.hasLocation()) {
          final device = dashboardProvider.selectedDevice!;
          mapCenter = LatLng(
            device.lastTelemetry!.latitude!,
            device.lastTelemetry!.longitude!,
          );
          mapZoom = 13.0;
        }
        // Otherwise if we have devices with location, fit the map to show all of them
        else if (dashboardProvider.devicesWithLocation.isNotEmpty) {
          // We'll handle this with the map bounds
          mapZoom = 9.0;
        }
        
        return Card(
          margin: const EdgeInsets.all(8.0),
          elevation: 4,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header with title and track controls
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Device Map',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (dashboardProvider.selectedDevice != null)
                      Row(
                        children: [
                          Text(
                            dashboardProvider.selectedDevice!.name ?? 
                            dashboardProvider.selectedDevice!.deviceId,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              color: Colors.blue,
                            ),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton.icon(
                            icon: Icon(_showTrack ? Icons.hide_source : Icons.timeline),
                            label: Text(_showTrack ? 'Hide Track' : 'Show Track'),
                            onPressed: () => _toggleTrack(dashboardProvider),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _showTrack ? Colors.red : Colors.blue,
                              foregroundColor: Colors.white,
                            ),
                          ),
                        ],
                      ),
                  ],
                ),
              ),
              
              // Map
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: FlutterMap(
                    mapController: _mapController,
                    options: MapOptions(
                      initialCenter: mapCenter,
                      initialZoom: mapZoom,
                      interactionOptions: InteractionOptions(
                        flags: InteractiveFlag.all,
                      ),
                    ),
                    children: [
                      // Base tile layer
                      TileLayer(
                        urlTemplate: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                        subdomains: const ['a', 'b', 'c'],
                        userAgentPackageName: 'com.tambreit.campovision',
                      ),
                      
                      // Device markers
                      MarkerLayer(
                        markers: _buildDeviceMarkers(dashboardProvider),
                      ),
                      
                      // Telemetry track polyline (only shown when a device is selected and track is enabled)
                      if (dashboardProvider.selectedDevice != null && _showTrack)
                        PolylineLayer(
                          polylines: [
                            Polyline(
                              points: _buildTrackPoints(dashboardProvider),
                              strokeWidth: 4.0,
                              color: Colors.blue.shade700,
                            ),
                          ],
                        ),
                      
                      // Track point markers if enabled
                      if (_showTrack && _deviceTelemetry.isNotEmpty)
                        MarkerLayer(
                          markers: _buildTrackMarkers(),
                        ),
                    ],
                  ),
                ),
              ),
              
              // Date range selector for track
              if (dashboardProvider.selectedDevice != null)
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => _selectDateRange(context),
                          child: Text(
                            'Date Range: ${_formatDateShort(_startDate)} - ${_formatDateShort(_endDate)}',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  // Helper method to build device markers
  List<Marker> _buildDeviceMarkers(DashboardProvider dashboardProvider) {
    return dashboardProvider.devicesWithLocation.map((device) {
      // Skip devices without location data
      if (!device.hasLocation()) return const Marker(point: LatLng(0, 0), child: SizedBox.shrink());
      
      final isSelected = dashboardProvider.selectedDevice?.deviceId == device.deviceId;
      
      return Marker(
        point: LatLng(
          device.lastTelemetry!.latitude!,
          device.lastTelemetry!.longitude!,
        ),
        width: 40,
        height: 40,
        child: GestureDetector(
          onTap: () {
            dashboardProvider.selectDevice(device);
            _showDeviceInfo(context, device);
          },
          child: Container(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isSelected ? Colors.blue.withOpacity(0.7) : Colors.blue.withOpacity(0.5),
              border: Border.all(
                color: isSelected ? Colors.white : Colors.blue,
                width: isSelected ? 2 : 1,
              ),
            ),
            child: const Icon(
              Icons.location_on,
              color: Colors.white,
            ),
          ),
        ),
      );
    }).toList();
  }
  
  // Helper method to build track points from telemetry data
  List<LatLng> _buildTrackPoints(DashboardProvider dashboardProvider) {
    if (dashboardProvider.selectedDevice == null || _deviceTelemetry.isEmpty) {
      return [];
    }
    
    return _deviceTelemetry
        .where((t) => t.latitude != null && t.longitude != null)
        .map((t) => LatLng(t.latitude!, t.longitude!))
        .toList();
  }
  
  // Build markers for track points
  List<Marker> _buildTrackMarkers() {
    final markers = <Marker>[];
    
    // Skip the first point (most recent) as it's already shown in the devices list
    for (int i = 1; i < _deviceTelemetry.length; i++) {
      final telemetry = _deviceTelemetry[i];
      
      if (telemetry.latitude == null || telemetry.longitude == null) continue;
      
      markers.add(
        Marker(
          point: LatLng(telemetry.latitude!, telemetry.longitude!),
          width: 20,
          height: 20,
          child: GestureDetector(
            onTap: () => _showTelemetryInfo(context, telemetry),
            child: Container(
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.red,
              ),
              child: const Icon(
                Icons.circle,
                color: Colors.white,
                size: 8,
              ),
            ),
          ),
        ),
      );
    }
    
    return markers;
  }
  
  // Toggle track visibility
  void _toggleTrack(DashboardProvider provider) async {
    if (provider.selectedDevice == null) return;
    
    setState(() {
      _showTrack = !_showTrack;
    });
    
    if (_showTrack) {
      _fetchDeviceTelemetry(provider);
    }
  }
  
  // Fetch telemetry data for the selected device
  Future<void> _fetchDeviceTelemetry(DashboardProvider provider) async {
    if (provider.selectedDevice == null) return;
    
    final telemetry = await provider.fetchDeviceTelemetry(
      provider.selectedDevice!.deviceId,
      startTime: _startDate,
      endTime: _endDate,
    );
    
    setState(() {
      _deviceTelemetry = telemetry;
    });
  }
  
  // Show device info popup
  void _showDeviceInfo(BuildContext context, Device device) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(device.name ?? device.deviceId),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (device.description != null)
              Text('Description: ${device.description}'),
            const SizedBox(height: 8),
            if (device.lastTelemetry?.temperature != null)
              Text('Temperature: ${device.lastTelemetry!.temperature}°C'),
            if (device.lastTelemetry?.humidity != null)
              Text('Humidity: ${device.lastTelemetry!.humidity}%'),
            const SizedBox(height: 8),
            Text('Last seen: ${_formatDate(device.lastTelemetry!.timestamp)}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
  
  // Show telemetry point info popup
  void _showTelemetryInfo(BuildContext context, Telemetry telemetry) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Historical Data'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Device: ${telemetry.deviceId}'),
            const SizedBox(height: 8),
            if (telemetry.temperature != null)
              Text('Temperature: ${telemetry.temperature}°C'),
            if (telemetry.humidity != null)
              Text('Humidity: ${telemetry.humidity}%'),
            const SizedBox(height: 8),
            Text('Time: ${_formatDate(telemetry.timestamp)}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
  
  // Select date range for telemetry data
  Future<void> _selectDateRange(BuildContext context) async {
    final initialDateRange = DateTimeRange(
      start: _startDate,
      end: _endDate,
    );
    
    final newDateRange = await showDateRangePicker(
      context: context,
      initialDateRange: initialDateRange,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now(),
    );
    
    if (newDateRange != null) {
      setState(() {
        _startDate = newDateRange.start;
        _endDate = newDateRange.end;
      });
      
      final provider = Provider.of<DashboardProvider>(context, listen: false);
      if (_showTrack && provider.selectedDevice != null) {
        _fetchDeviceTelemetry(provider);
      }
    }
  }
  
  // Format date for display
  String _formatDate(String timestamp) {
    final date = DateTime.parse(timestamp);
    return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }
  
  // Format date for short display
  String _formatDateShort(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}
