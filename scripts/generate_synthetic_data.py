#!/usr/bin/env python3
"""
Generate synthetic data for Campo Vision DynamoDB tables.
This script creates related data across Company, Device, Telemetry, and UserCompany tables.
"""

import csv
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
import os
import boto3
from decimal import Decimal
import argparse
import time

# Define timezone (UTC-3)
LOCAL_TIMEZONE = timezone(timedelta(hours=-3))

# Company data
COMPANY_NAMES = [
    "AgriTech Solutions", "FarmWise Systems", "Campo Innovations", 
    "HarvestTrack", "CropMonitor Inc.", "TerraFarm Technologies",
    "AgroVision", "FieldSense", "RuralTech Solutions", "GreenHarvest"
]

# Device types
DEVICE_TYPES = ["Tractor", "Harvester", "Sprayer", "Drone", "Sensor", "Irrigation System"]

# Device models
DEVICE_MODELS = {
    "Tractor": ["T-1000", "T-2000", "T-3000", "FarmMaster 500", "AgriPower X1"],
    "Harvester": ["H-500", "H-750", "H-1000", "CropCollector Pro", "HarvestKing"],
    "Sprayer": ["S-100", "S-200", "S-300", "PrecisionSpray", "FieldMist"],
    "Drone": ["D-100", "D-200", "D-300", "AerialScout", "FieldView Pro"],
    "Sensor": ["WeatherSense", "SoilMonitor", "MoisturePro", "TempTracker", "FieldEye"],
    "Irrigation System": ["I-500", "I-750", "I-1000", "WaterWise", "HydroControl"]
}

# Regions with latitude/longitude bounds (approximate)
REGIONS = {
    "Uruguay Florida": {"lat": (-34.1, -33.9), "lon": (-56.25, -56.15)}
}

def generate_company_data(num_companies):
    """Generate synthetic company data"""
    companies = []
    
    for i in range(num_companies):
        company_id = f"comp-{uuid.uuid4()}"
        company_name = random.choice(COMPANY_NAMES) if i >= len(COMPANY_NAMES) else COMPANY_NAMES[i]
        region = random.choice(list(REGIONS.keys()))
        
        company = {
            "companyId": company_id,
            "name": company_name,
            "region": region,
            "contactEmail": f"contact@{company_name.lower().replace(' ', '')}.com",
            "subscriptionTier": random.choice(["Basic", "Standard", "Premium"]),
            "createdAt": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat() + "Z"
        }
        companies.append(company)
    
    return companies

def generate_device_data(companies, num_devices_per_company):
    """Generate synthetic device data linked to companies"""
    devices = []
    
    for company in companies:
        company_id = company["companyId"]
        region = company["region"]
        region_bounds = REGIONS[region]
        
        for i in range(num_devices_per_company):
            device_id = f"dev-{uuid.uuid4()}"
            device_type = random.choice(DEVICE_TYPES)
            
            device = {
                "deviceId": device_id,
                "companyId": company_id,
                "name": f"{device_type}-{i+1}",
                "type": device_type,
                "model": random.choice(DEVICE_MODELS[device_type]),
                "status": random.choice(["Active", "Maintenance", "Inactive"]),
                "lastKnownLatitude": round(random.uniform(region_bounds["lat"][0], region_bounds["lat"][1]), 6),
                "lastKnownLongitude": round(random.uniform(region_bounds["lon"][0], region_bounds["lon"][1]), 6),
                "registeredAt": (datetime.now() - timedelta(days=random.randint(1, 300))).isoformat() + "Z"
            }
            devices.append(device)
    
    return devices

def generate_telemetry_data(devices, days_of_data, readings_per_day, last_hour=False):
    """Generate synthetic telemetry data linked to devices
    
    Args:
        devices: List of device dictionaries
        days_of_data: Number of days to generate data for
        readings_per_day: Number of readings per day for each device
        last_hour: If True, generate data only for the last hour instead of days
    """
    telemetry_data = []
    
    for device in devices:
        device_id = device["deviceId"]
        device_type = device["type"]
        region = None
        
        # Find the region for this device by looking up its company
        for company in companies:
            if company["companyId"] == device["companyId"]:
                region = company["region"]
                break
        
        if not region:
            continue
            
        region_bounds = REGIONS[region]
        
        # Base coordinates near the last known position
        base_lat = device["lastKnownLatitude"]
        base_lon = device["lastKnownLongitude"]
        
        # Generate telemetry based on time range
        if last_hour:
            # Generate data for the last hour only
            # Use local timezone (UTC-3) instead of UTC
            current_time = datetime.now(LOCAL_TIMEZONE)
            start_time = current_time - timedelta(hours=1)
            
            # Calculate number of readings to generate in the last hour
            # Default to one reading every 5 minutes = 12 readings per hour
            num_readings = readings_per_day if readings_per_day <= 12 else 12
            
            for reading in range(num_readings):
                # Distribute readings evenly across the last hour
                minutes_ago = int(60 / num_readings * reading)
                timestamp_dt = current_time - timedelta(minutes=minutes_ago)
                # Add some randomness to seconds and microseconds
                timestamp_dt = timestamp_dt.replace(second=random.randint(0, 59), microsecond=random.randint(0, 999999))
                # Convert to UTC for storage (adding Z suffix indicates UTC)
                timestamp_utc = timestamp_dt.astimezone(timezone.utc)
                timestamp = timestamp_utc.isoformat().replace('+00:00', 'Z')
                
                # Simulate movement within a small radius
                # More movement for mobile devices, less for stationary ones
                movement_factor = 0.01 if device_type in ["Tractor", "Harvester", "Sprayer", "Drone"] else 0.001
                lat = round(base_lat + random.uniform(-movement_factor, movement_factor), 6)
                lon = round(base_lon + random.uniform(-movement_factor, movement_factor), 6)
                
                # Ensure coordinates stay within region bounds
                lat = max(region_bounds["lat"][0], min(region_bounds["lat"][1], lat))
                lon = max(region_bounds["lon"][0], min(region_bounds["lon"][1], lon))
                
                # Generate temperature based on device type and random variation
                base_temp = 25  # Base temperature in Celsius
                if device_type in ["Tractor", "Harvester"]:
                    # Engines run hot
                    temp = round(base_temp + random.uniform(10, 30), 1)
                elif device_type == "Sensor":
                    # Ambient temperature with slight variation
                    temp = round(base_temp + random.uniform(-5, 5), 1)
                else:
                    # Other devices with moderate heat
                    temp = round(base_temp + random.uniform(0, 15), 1)
                
                # Add speed field based on device type
                speed = None
                
                if device_type == "Tractor" or device_type == "Harvester":
                    speed = round(random.uniform(0, 30), 1)  # km/h
                elif device_type == "Drone":
                    speed = round(random.uniform(0, 40), 1)  # km/h
                # For other device types, speed might be 0 or not applicable
                elif device_type in ["Sprayer", "Sensor", "Irrigation System"]:
                    # Only some devices have speed
                    if device_type == "Sprayer":
                        speed = round(random.uniform(0, 20), 1)  # km/h
                    else:
                        speed = 0.0  # Stationary devices
                        
                # Parse the timestamp to calculate TTL (expiration time)
                try:
                    # Convert ISO timestamp to datetime object
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    
                    # Calculate expiration time (timestamp + 1 hour)
                    expiration_time = dt + timedelta(hours=4)
                    
                    # Convert to Unix timestamp (seconds since epoch) for DynamoDB TTL
                    ttl_value = int(expiration_time.timestamp())
                except Exception:
                    # Fallback: use current time + 1 hour if there's an issue
                    ttl_value = int(time.time()) + 3600  # 3600 seconds = 1 hour
                
                telemetry = {
                    "deviceId": device_id,
                    "timestamp": timestamp,
                    "latitude": lat,
                    "longitude": lon,
                    "temperature": temp,
                    "ttl": ttl_value
                }
                
                # Add speed if available
                if speed is not None:
                    telemetry["speed"] = speed
                
                telemetry_data.append(telemetry)
        else:
            # Generate telemetry for each day
            for day in range(days_of_data):
                # Use local timezone (UTC-3) instead of UTC
                date = datetime.now(LOCAL_TIMEZONE) - timedelta(days=day)
                
                # Generate multiple readings per day
                for reading in range(readings_per_day):
                    # Time progression throughout the day
                    hour = random.randint(6, 20)  # Working hours
                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    microsecond = random.randint(0, 999999)  # Add microseconds for uniqueness
                    # Create timestamp with local timezone then convert to UTC for storage
                    local_dt = date.replace(hour=hour, minute=minute, second=second, microsecond=microsecond)
                    utc_dt = local_dt.astimezone(timezone.utc)
                    timestamp = utc_dt.isoformat().replace('+00:00', 'Z')
                    
                    # Simulate movement within a small radius
                    # More movement for mobile devices, less for stationary ones
                    movement_factor = 0.01 if device_type in ["Tractor", "Harvester", "Sprayer", "Drone"] else 0.001
                    lat = round(base_lat + random.uniform(-movement_factor, movement_factor), 6)
                    lon = round(base_lon + random.uniform(-movement_factor, movement_factor), 6)
                    
                    # Ensure coordinates stay within region bounds
                    lat = max(region_bounds["lat"][0], min(region_bounds["lat"][1], lat))
                    lon = max(region_bounds["lon"][0], min(region_bounds["lon"][1], lon))
                    
                    # Generate temperature based on device type and random variation
                    base_temp = 25  # Base temperature in Celsius
                    if device_type in ["Tractor", "Harvester"]:
                        # Engines run hot
                        temp = round(base_temp + random.uniform(10, 30), 1)
                    elif device_type == "Sensor":
                        # Ambient temperature with slight variation
                        temp = round(base_temp + random.uniform(-5, 5), 1)
                    else:
                        # Other devices with moderate heat
                        temp = round(base_temp + random.uniform(0, 15), 1)
                    
                    # Add speed field based on device type
                    speed = None
                    
                    if device_type == "Tractor" or device_type == "Harvester":
                        speed = round(random.uniform(0, 30), 1)  # km/h
                    elif device_type == "Drone":
                        speed = round(random.uniform(0, 40), 1)  # km/h
                    # For other device types, speed might be 0 or not applicable
                    elif device_type in ["Sprayer", "Sensor", "Irrigation System"]:
                        # Only some devices have speed
                        if device_type == "Sprayer":
                            speed = round(random.uniform(0, 20), 1)  # km/h
                        else:
                            speed = 0.0  # Stationary devices
                
                    # Parse the timestamp to calculate TTL (expiration time)
                    try:
                        # Convert ISO timestamp to datetime object
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        
                        # Calculate expiration time (timestamp + 1 hour)
                        expiration_time = dt + timedelta(hours=1)
                        
                        # Convert to Unix timestamp (seconds since epoch) for DynamoDB TTL
                        ttl_value = int(expiration_time.timestamp())
                    except Exception:
                        # Fallback: use current time + 1 hour if there's an issue
                        ttl_value = int(time.time()) + 3600  # 3600 seconds = 1 hour
                    
                    telemetry = {
                        "deviceId": device_id,
                        "timestamp": timestamp,
                        "latitude": lat,
                        "longitude": lon,
                        "temperature": temp,
                        "ttl": ttl_value
                    }
                    
                    # Add speed if available
                    if speed is not None:
                        telemetry["speed"] = speed
                    
                    telemetry_data.append(telemetry)
    
    # Sort by timestamp
    telemetry_data.sort(key=lambda x: x["timestamp"])
    return telemetry_data

def write_to_csv(data, filename):
    """Write data to CSV file"""
    if not data:
        return
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Get all possible fieldnames from all records
    fieldnames = set()
    for row in data:
        fieldnames.update(row.keys())
    fieldnames = sorted(list(fieldnames))
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    
    print(f"Created {filename} with {len(data)} records")

def write_to_json(data, filename):
    """Write data to JSON file"""
    if not data:
        return
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=2)
    
    print(f"Created {filename} with {len(data)} records")

def generate_user_company_data(companies, user_id):
    """Generate user-company relationships for a specific user ID"""
    user_company_data = []
    timestamp = datetime.now().isoformat() + "Z"
    
    for company in companies:
        user_company = {
            "userId": user_id,
            "companyId": company["companyId"],
            "role": "admin",  # Assign admin role to the user for all companies
            "createdBy": user_id,  # Self-created
            "createdAt": timestamp,
            "updatedAt": timestamp
        }
        user_company_data.append(user_company)
    
    return user_company_data

def import_to_dynamodb(data, table_name, endpoint_url=None):
    """Import data to DynamoDB table"""
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
        table = dynamodb.Table(table_name)
        
        # Convert data to DynamoDB format (handling Decimal types)
        items = []
        for item in data:
            dynamodb_item = {}
            for key, value in item.items():
                if isinstance(value, float):
                    dynamodb_item[key] = Decimal(str(value))
                else:
                    dynamodb_item[key] = value
            items.append(dynamodb_item)
        
        # Import data in batches
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
        
        print(f"Imported {len(items)} items to {table_name}")
        return True
    except Exception as e:
        print(f"Error importing data to DynamoDB: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate synthetic data for Campo Vision')
    parser.add_argument('--companies', type=int, default=5, help='Number of companies to generate')
    parser.add_argument('--devices', type=int, default=3, help='Number of devices per company')
    parser.add_argument('--days', type=int, default=7, help='Days of telemetry data to generate')
    parser.add_argument('--readings', type=int, default=24, help='Readings per day for each device')
    parser.add_argument('--last-hour', action='store_true', help='Generate telemetry data for only the last hour (overrides --days)')
    parser.add_argument('--import-data', action='store_true', help='Import data to DynamoDB')
    parser.add_argument('--local-db', action='store_true', help='Use local DynamoDB endpoint')
    parser.add_argument('--user-id', type=str, default="144884f8-2071-7098-27eb-6309b76fc5e6", 
                        help='User ID to associate with companies (default: 144884f8-2071-7098-27eb-6309b76fc5e6)')
    args = parser.parse_args()

    # Generate data
    print(f"Generating data for {args.companies} companies with {args.devices} devices each...")
    if args.last_hour:
        print(f"Each device will have telemetry data for the last hour with up to {args.readings} readings")
    else:
        print(f"Each device will have {args.days} days of data with {args.readings} readings per day")
    print(f"Companies will be associated with user ID: {args.user_id}")
    
    companies = generate_company_data(args.companies)
    devices = generate_device_data(companies, args.devices)
    telemetry = generate_telemetry_data(devices, args.days, args.readings, args.last_hour)
    user_company = generate_user_company_data(companies, args.user_id)
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Write to CSV files
    write_to_csv(companies, 'data/companies.csv')
    write_to_csv(devices, 'data/devices.csv')
    write_to_csv(telemetry, 'data/telemetry.csv')
    write_to_csv(user_company, 'data/user_company.csv')
    
    # Write to JSON files (useful for importing to DynamoDB)
    write_to_json(companies, 'data/companies.json')
    write_to_json(devices, 'data/devices.json')
    write_to_json(telemetry, 'data/telemetry.json')
    write_to_json(user_company, 'data/user_company.json')
    
    # Import to DynamoDB if requested
    if args.import_data:
        endpoint_url = 'http://localhost:8000' if args.local_db else None
        
        # CloudFormation stack table names
        company_table = 'campo-vision-CompanyTable-1VBJGXKYZKXKO'
        device_table = 'campo-vision-DeviceTable-Y0THVJX31BEI'
        telemetry_table = 'campo-vision-TelemetryTable-NGA2PSH16WWQ'
        user_company_table = 'campo-vision-UserCompanyTable-1JAHRFRT6W5YZ'
        
        # Use local table names if using local DynamoDB
        if args.local_db:
            company_table = 'CompanyTable'
            device_table = 'DeviceTable'
            telemetry_table = 'TelemetryTable'
            user_company_table = 'UserCompanyTable'
        
        print("Importing data to DynamoDB...")
        import_to_dynamodb(companies, company_table, endpoint_url)
        import_to_dynamodb(devices, device_table, endpoint_url)
        import_to_dynamodb(telemetry, telemetry_table, endpoint_url)
        import_to_dynamodb(user_company, user_company_table, endpoint_url)
        print(f"Successfully associated {len(companies)} companies with user ID: {args.user_id}")
