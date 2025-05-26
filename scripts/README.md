# Campo Vision Synthetic Data Generator

This directory contains scripts for generating synthetic data for the Campo Vision DynamoDB tables.

## Overview

The `generate_synthetic_data.py` script creates related synthetic data for:

1. **Companies** - Agricultural companies using the Campo Vision system
2. **Devices** - IoT devices owned by these companies (tractors, harvesters, sensors, etc.)
3. **Telemetry** - Time-series data from these devices including location, temperature, and device-specific metrics

The data is generated with realistic relationships between tables and appropriate values for each device type.

## Usage

### Basic Usage

Generate default data (5 companies, 3 devices per company, 7 days of data with 24 readings per day):

```bash
python generate_synthetic_data.py
```

This will create CSV and JSON files in a `data/` directory.

### Custom Data Generation

Customize the amount of data generated:

```bash
python generate_synthetic_data.py --companies 10 --devices 5 --days 14 --readings 48
python generate_synthetic_data.py --companies 2 --devices 2 --days 2 --readings 5 --import-data
```

### Import to DynamoDB

To import the generated data directly to DynamoDB:

```bash
# For AWS DynamoDB
python generate_synthetic_data.py --import-data

# For local DynamoDB (e.g., DynamoDB Local)
python generate_synthetic_data.py --import-data --local-db
```

## Data Structure

### Companies Table

- `companyId` - Unique identifier (primary key)
- `name` - Company name
- `region` - Geographic region of operation
- `contactEmail` - Contact email address
- `subscriptionTier` - Subscription level (Basic, Standard, Premium)
- `createdAt` - Account creation timestamp

### Devices Table

- `deviceId` - Unique device identifier (primary key)
- `companyId` - Company that owns the device (sort key)
- `name` - Device name
- `type` - Device type (Tractor, Harvester, Sprayer, Drone, Sensor, Irrigation System)
- `model` - Specific model of the device
- `status` - Current status (Active, Maintenance, Inactive)
- `lastKnownLatitude` - Last recorded latitude
- `lastKnownLongitude` - Last recorded longitude
- `registeredAt` - Device registration timestamp

### Telemetry Table

- `deviceId` - Device identifier (primary key)
- `timestamp` - Timestamp of the reading (sort key)
- `latitude` - GPS latitude
- `longitude` - GPS longitude
- `temperature` - Temperature reading in Celsius
- Additional device-specific fields:
  - Tractors/Harvesters: `engineRpm`, `fuelLevel`, `speed`
  - Drones: `batteryLevel`, `altitude`, `speed`
  - Sensors: `soilMoisture`, `humidity`, `lightLevel`
  - Irrigation Systems: `waterFlow`, `pressure`, `valveStatus`

## Notes

- The script ensures that device locations are within realistic bounds for their company's region
- Telemetry data includes realistic variations based on device type
- All timestamps use ISO 8601 format with UTC timezone (ending in 'Z')
