import 'package:flutter/material.dart';
import '../models/device.dart';

class DeviceDetailsPanel extends StatelessWidget {
  final Device device;
  final VoidCallback onClose;

  const DeviceDetailsPanel({
    Key? key,
    required this.device,
    required this.onClose,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // Use LayoutBuilder to constrain the panel height
    return LayoutBuilder(
      builder: (context, constraints) {
        // Calculate a reasonable max height for the panel
        // This ensures it doesn't try to expand beyond the available space
        final maxHeight = MediaQuery.of(context).size.height * 0.4;
        
        return Container(
          constraints: BoxConstraints(
            maxHeight: maxHeight,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min, // Don't try to take all available space
            children: [
              // Header with title and close button
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 6.0),
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
                    Expanded(
                      child: Text(
                        device.name ?? 'Device Details',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                          overflow: TextOverflow.ellipsis,
                        ),
                        maxLines: 1,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white, size: 18),
                      onPressed: onClose,
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
              ),
              
              // Device details content - use Flexible instead of Expanded
              Flexible(
                child: Container(
                  color: Theme.of(context).cardColor,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(10.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [

                        
                        // Device ID
                        Text(
                          'Device ID: ${device.deviceId}',
                          style: TextStyle(
                            fontSize: 12,
                            color: Theme.of(context).textTheme.bodyMedium?.color?.withOpacity(0.7),
                          ),
                        ),
                        const SizedBox(height: 10),
                        
                        // Description
                        if (device.description != null && device.description!.isNotEmpty) ...[                    
                          const Text(
                            'Description:',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(device.description!, style: const TextStyle(fontSize: 12)),
                          const SizedBox(height: 8),
                        ],
                        
                        // Last seen
                        if (device.lastTelemetry != null) ...[                    
                          const Text(
                            'Last Telemetry:',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 8),
                          
                          // Last seen time
                          Row(
                            children: [
                              const Icon(Icons.access_time, size: 16),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  _formatDate(device.lastTelemetry!.timestamp),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          
                          // Location
                          if (device.hasLocation()) ...[                      
                            Row(
                              children: [
                                const Icon(Icons.location_on, size: 16),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'Lat: ${device.lastTelemetry!.latitude!.toStringAsFixed(6)}, ' +
                                    'Lng: ${device.lastTelemetry!.longitude!.toStringAsFixed(6)}',
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                          ],
                          
                          // Temperature
                          if (device.lastTelemetry!.temperature != null) ...[                      
                            Row(
                              children: [
                                const Icon(Icons.thermostat, size: 16),
                                const SizedBox(width: 8),
                                Text('Temperature: ${device.lastTelemetry!.temperature}°C'),
                              ],
                            ),
                            const SizedBox(height: 8),
                          ],
                          
                          // Humidity
                          if (device.lastTelemetry!.humidity != null) ...[                      
                            Row(
                              children: [
                                const Icon(Icons.water_drop, size: 16),
                                const SizedBox(width: 8),
                                Text('Humidity: ${device.lastTelemetry!.humidity}%'),
                              ],
                            ),
                            const SizedBox(height: 8),
                          ],
                        ],
                        
                        // Action buttons section removed
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
  
  // Format date for display
  String _formatDate(String timestamp) {
    final date = DateTime.parse(timestamp);
    return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }
}
