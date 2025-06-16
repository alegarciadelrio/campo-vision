import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';
import 'dart:math' show log, ln2;
import '../models/device.dart';
import '../providers/dashboard_provider.dart';

// Singleton to access DeviceMap functionality from anywhere
class DeviceMapController {
  static final DeviceMapController _instance = DeviceMapController._internal();
  
  factory DeviceMapController() {
    return _instance;
  }
  
  DeviceMapController._internal();
  
  _DeviceMapState? _mapState;
  
  void _registerState(_DeviceMapState state) {
    _mapState = state;
  }
  
  void _unregisterState(_DeviceMapState state) {
    if (_mapState == state) {
      _mapState = null;
    }
  }
  
  // Public method to focus on a device
  void focusOnDevice(Device device) {
    if (_mapState != null) {
      _mapState!.focusOnDevice(device);
    }
  }
}

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
  final DeviceMapController _controller = DeviceMapController();
  
  @override
  void initState() {
    super.initState();
    // Register this state with the controller
    _controller._registerState(this);
    
    // Add a post-frame callback to fit all devices after the first build
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _fitAllDevices();
    });
  }
  
  // Method to fit all devices on the map
  void _fitAllDevices() {
    final dashboardProvider = Provider.of<DashboardProvider>(context, listen: false);
    if (dashboardProvider.devicesWithLocation.isEmpty) return;
    
    // Collect all device locations
    final points = <LatLng>[];
    for (final device in dashboardProvider.devicesWithLocation) {
      if (device.hasLocation()) {
        points.add(LatLng(
          device.lastTelemetry!.latitude!,
          device.lastTelemetry!.longitude!,
        ));
      }
    }
    
    if (points.isEmpty) return;
    
    // If there's only one point, center on it with a reasonable zoom
    if (points.length == 1) {
      _mapController.move(points.first, 10.0); // Lower zoom level (10 instead of 13)
      return;
    }
    
    // Calculate bounds to fit all points
    double minLat = 90.0;
    double maxLat = -90.0;
    double minLng = 180.0;
    double maxLng = -180.0;
    
    for (final point in points) {
      minLat = point.latitude < minLat ? point.latitude : minLat;
      maxLat = point.latitude > maxLat ? point.latitude : maxLat;
      minLng = point.longitude < minLng ? point.longitude : minLng;
      maxLng = point.longitude > maxLng ? point.longitude : maxLng;
    }
    
    // Calculate center point
    final centerLat = (minLat + maxLat) / 2;
    final centerLng = (minLng + maxLng) / 2;
    
    // Calculate the distance between the furthest points
    final latDistance = (maxLat - minLat).abs();
    final lngDistance = (maxLng - minLng).abs();
    
    // Use a simple heuristic for zoom level based on the distance
    // The larger the distance, the smaller the zoom level
    double zoom = 12.0; // Default zoom
    
    if (latDistance > 0.5 || lngDistance > 0.5) {
      zoom = 9.0;
    }
    if (latDistance > 1.0 || lngDistance > 1.0) {
      zoom = 8.0;
    }
    if (latDistance > 2.0 || lngDistance > 2.0) {
      zoom = 7.0;
    }
    if (latDistance > 5.0 || lngDistance > 5.0) {
      zoom = 6.0;
    }
    if (latDistance > 10.0 || lngDistance > 10.0) {
      zoom = 5.0;
    }
    if (latDistance > 20.0 || lngDistance > 20.0) {
      zoom = 4.0;
    }
    
    // Move the map to show all points with a lower zoom level for better visibility
    _mapController.move(LatLng(centerLat, centerLng), zoom);
  }
  
  // This method is no longer used - we're using a simpler heuristic approach instead
  
  @override
  void dispose() {
    // Unregister this state when disposed
    _controller._unregisterState(this);
    super.dispose();
  }
  
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
          // Calculate the center of all devices with location
          double sumLat = 0;
          double sumLng = 0;
          int count = 0;
          
          for (final device in dashboardProvider.devicesWithLocation) {
            if (device.hasLocation()) {
              sumLat += device.lastTelemetry!.latitude!;
              sumLng += device.lastTelemetry!.longitude!;
              count++;
            }
          }
          
          if (count > 0) {
            mapCenter = LatLng(sumLat / count, sumLng / count);
            mapZoom = 9.0;
          }
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
                          const SizedBox(width: 8),
                          OutlinedButton(
                            onPressed: () => _selectDateRange(context),
                            child: Text(
                              'Date Range: ${_formatDateShort(_startDate)} - ${_formatDateShort(_endDate)}',
                              style: const TextStyle(fontSize: 12),
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
                        urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        // Removed subdomains to avoid OSM warning
                        userAgentPackageName: 'com.tambreit.campovision',
                      ),
                      
                      // Device markers
                      MarkerLayer(
                        markers: _buildDeviceMarkers(dashboardProvider),
                      ),
                      
                      // Telemetry track polyline (only shown when a device is selected and track is enabled)
                      if (dashboardProvider.selectedDevice != null && _showTrack && _buildTrackPoints(dashboardProvider).isNotEmpty)
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
              
              // Date range selector moved next to show track button
            ],
          ),
        );
      },
    );
  }

  // Helper method to build device markers
  List<Marker> _buildDeviceMarkers(DashboardProvider dashboardProvider) {
    // If a device is selected, only show that device
    final devices = dashboardProvider.selectedDevice != null
        ? dashboardProvider.devicesWithLocation
            .where((d) => d.deviceId == dashboardProvider.selectedDevice!.deviceId)
            .toList()
        : dashboardProvider.devicesWithLocation;
            
    return devices.map((device) {
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
            _focusOnDeviceInternal(device);
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
      // Return a list with at least one point to avoid LatLngBounds error
      // when creating bounds from an empty list
      return [];
    }
    
    final points = _deviceTelemetry
        .where((t) => t.latitude != null && t.longitude != null)
        .map((t) => LatLng(t.latitude!, t.longitude!))
        .toList();
        
    // If no valid points were found, return an empty list
    // The PolylineLayer will handle this correctly
    return points;
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
  
  // Public method to focus on a device that can be called from outside
  void focusOnDevice(Device device) {
    if (!device.hasLocation()) return;
    
    // Select the device in the provider
    final dashboardProvider = Provider.of<DashboardProvider>(context, listen: false);
    dashboardProvider.selectDevice(device);
    
    // Ensure the device is shown on the map
    setState(() {
      // This will trigger a rebuild with the filtered device list
    });
    
    // Focus the map on the device
    _focusOnDeviceInternal(device);
  }
  
  // Internal method to focus map on a specific device
  void _focusOnDeviceInternal(Device device) {
    if (!device.hasLocation()) return;
    
    // Animate to the device's position with a higher zoom level
    _mapController.move(
      LatLng(device.lastTelemetry!.latitude!, device.lastTelemetry!.longitude!),
      15.0, // Higher zoom level for better focus
    );
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
