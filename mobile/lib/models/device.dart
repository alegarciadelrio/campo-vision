class Device {
  final String deviceId;
  final String? name;
  final String? description;
  final String companyId;
  final Telemetry? lastTelemetry;

  Device({
    required this.deviceId,
    this.name,
    this.description,
    required this.companyId,
    this.lastTelemetry,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      deviceId: json['deviceId'],
      name: json['name'],
      description: json['description'],
      companyId: json['companyId'],
      lastTelemetry: json['lastTelemetry'] != null
          ? Telemetry.fromJson(json['lastTelemetry'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'deviceId': deviceId,
      'name': name,
      'description': description,
      'companyId': companyId,
      'lastTelemetry': lastTelemetry?.toJson(),
    };
  }

  bool hasLocation() {
    return lastTelemetry != null &&
        lastTelemetry!.latitude != null &&
        lastTelemetry!.longitude != null;
  }
}

class Telemetry {
  final String deviceId;
  final double? temperature;
  final double? humidity;
  final double? latitude;
  final double? longitude;
  final String timestamp;

  Telemetry({
    required this.deviceId,
    this.temperature,
    this.humidity,
    this.latitude,
    this.longitude,
    required this.timestamp,
  });

  factory Telemetry.fromJson(Map<String, dynamic> json) {
    return Telemetry(
      deviceId: json['deviceId'],
      temperature: json['temperature'] != null ? json['temperature'].toDouble() : null,
      humidity: json['humidity'] != null ? json['humidity'].toDouble() : null,
      latitude: json['latitude'] != null ? json['latitude'].toDouble() : null,
      longitude: json['longitude'] != null ? json['longitude'].toDouble() : null,
      timestamp: json['timestamp'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'deviceId': deviceId,
      'temperature': temperature,
      'humidity': humidity,
      'latitude': latitude,
      'longitude': longitude,
      'timestamp': timestamp,
    };
  }
}
