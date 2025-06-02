# Campo Vision Scripts

This directory contains utility scripts for the Campo Vision project.

## Scripts Overview

### Device Certificate Creation (`create_device_certificate.py`)

This script generates X.509 certificates for IoT devices and registers them with AWS IoT Core.

#### Basic Usage

```bash
python create_device_certificate.py --device-id <device-id> [--company-id <company-id>] [--skip-dynamodb]
```

Example:
```bash
python create_device_certificate.py --device-id dev-tractor-123 --company-id comp-a786e492-4883-4ade-b948-a818c2465fd8
```

The script will:
1. Create an IoT Thing in AWS IoT Core
2. Generate device certificates
3. Attach the certificates to the Thing
4. Add the Thing to the CampoVisionDevices Thing Group
5. Register the device in DynamoDB (unless --skip-dynamodb is specified)

### IoT Thing Group Management (`manage_device_groups.py`)

This script manages AWS IoT Thing Groups for Campo Vision devices.

#### Basic Usage

```bash
# Add a device to a Thing Group
python manage_device_groups.py --add-device <device-id> [--group-name <group-name>]

# Remove a device from a Thing Group
python manage_device_groups.py --remove-device <device-id> [--group-name <group-name>]

# List devices in a Thing Group
python manage_device_groups.py --list-devices [--group-name <group-name>]

# List all Thing Groups
python manage_device_groups.py --list-groups

# Add all existing devices to a Thing Group
python manage_device_groups.py --add-all-devices [--group-name <group-name>]
```

If `--group-name` is not specified, the script will use the default group name from the `.env` file or `CampoVisionDevices`.

### MQTT Telemetry Sender (`send_mqtt_telemetry.py`)

This script sends telemetry data to AWS IoT Core using the MQTT protocol, which is more efficient than the REST API for IoT applications.

#### Basic Usage

```bash
python send_mqtt_telemetry.py --device-id <device-id> [--interval <seconds>] [--count <number>]
```

Example:
```bash
python send_mqtt_telemetry.py --device-id dev-tractor-123 --interval 5 --count 10
```

The script will:
1. Connect to AWS IoT Core using the device's certificates
2. Generate synthetic telemetry data (location, temperature, etc.)
3. Send the data to the `campo-vision/telemetry` topic
4. Repeat at the specified interval for the specified count (or indefinitely if count is not specified)

**Note:** Before using this script, you must first create device certificates using `create_device_certificate.py`.

### REST API Telemetry Sender (`send_telemetry.py`)

This script sends telemetry data to the Campo Vision API using HTTP requests.

### Synthetic Data Generator (`generate_synthetic_data.py`)

This script creates related synthetic data for:

1. **Companies** - Agricultural companies using the Campo Vision system
2. **Devices** - IoT devices owned by these companies (tractors, harvesters, sensors, etc.)
3. **Telemetry** - Time-series data from these devices including location, temperature, and device-specific metrics

The data is generated with realistic relationships between tables and appropriate values for each device type.

#### Basic Usage

Generate default data (5 companies, 3 devices per company, 7 days of data with 24 readings per day):

```bash
python generate_synthetic_data.py
```

This will create CSV and JSON files in a `data/` directory.

#### Custom Data Generation

Customize the amount of data generated:

```bash
python scripts/generate_synthetic_data.py --companies 10 --devices 5 --days 14 --readings 48
python scripts/generate_synthetic_data.py --companies 2 --devices 2 --days 2 --readings 5 --import-data
python3 scripts/generate_synthetic_data.py --companies 1 --devices 2 --readings 14 --last-hour --import-data
```

#### Import to DynamoDB

To import the generated data directly to DynamoDB:

```bash
# For AWS DynamoDB
python generate_synthetic_data.py --import-data

# For local DynamoDB (e.g., DynamoDB Local)
python generate_synthetic_data.py --import-data --local-db
```

#### Data Structure

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

#### Notes

- The script ensures that device locations are within realistic bounds for their company's region
- Telemetry data includes realistic variations based on device type
- All timestamps use ISO 8601 format with UTC timezone (ending in 'Z')

### DynamoDB Table Cleaner (`clear_dynamodb_tables.py`)

This script helps you identify and clear data from DynamoDB tables in your AWS account that are part of the Campo Vision project.

#### Usage

List all DynamoDB tables without clearing any data:

```bash
python clear_dynamodb_tables.py --list-only
```

Interactively select tables to clear (recommended):

```bash
python clear_dynamodb_tables.py
```

Specify AWS profile and region:

```bash
python clear_dynamodb_tables.py --profile default --region us-east-1
```

Clear specific tables directly:

```bash
python clear_dynamodb_tables.py --tables Table1 Table2 Table3
```

#### Features

- Automatically discovers all DynamoDB tables in your AWS account
- Identifies tables that are likely part of the Campo Vision project
- Interactive selection of tables to clear
- Confirmation prompt before deleting any data
- Efficiently scans and deletes all items from selected tables
- Uses batch operations to minimize API calls
- Provides progress updates during deletion
- Handles tables with composite keys (hash + range keys)
- Reports detailed statistics on deletion operations
