#!/usr/bin/env python3
"""
MQTT Telemetry Sender for Campo Vision

This script sends telemetry data to AWS IoT Core using MQTT protocol.
It uses device certificates for authentication and can generate synthetic data
for testing purposes.

Usage:
  python send_mqtt_telemetry.py --device-id <device-id> [--interval <seconds>] [--count <number>]
  
Example:
  python send_mqtt_telemetry.py --device-id dev-massey-ferguson-178 --interval 5 --count 10
"""

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

def setup_mqtt_client(device_id):
    """
    Set up and configure the MQTT client with the device's certificates
    
    Args:
        device_id (str): Device ID to use for connection
        
    Returns:
        AWSIoTMQTTClient: Configured MQTT client
    """
    # Get certificate paths
    cert_dir = Path(__file__).parent / "certificates" / device_id
    
    if not cert_dir.exists():
        raise FileNotFoundError(f"Certificate directory not found for device {device_id}. "
                               f"Please run create_device_certificate.py first.")
    
    # Load config
    config_path = cert_dir / "config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Get endpoint from config or environment
    endpoint = config.get('endpoint', os.environ.get('IOT_ENDPOINT'))
    
    if not endpoint:
        raise ValueError("IoT endpoint not found in config or environment variables")
    
    # Certificate paths
    cert_path = cert_dir / "certificate.pem"
    private_key_path = cert_dir / "private.key"
    
    # Check if certificates exist
    if not cert_path.exists() or not private_key_path.exists():
        raise FileNotFoundError(f"Certificate files not found for device {device_id}")
    
    # Get AWS IoT root CA
    root_ca_path = Path(__file__).parent / "certificates" / "AmazonRootCA1.pem"
    
    # Download root CA if it doesn't exist
    if not root_ca_path.exists():
        import requests
        logger.info("Downloading AWS IoT Root CA certificate...")
        root_ca_dir = root_ca_path.parent
        root_ca_dir.mkdir(exist_ok=True)
        
        response = requests.get("https://www.amazontrust.com/repository/AmazonRootCA1.pem")
        with open(root_ca_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Root CA certificate saved to {root_ca_path}")
    
    # Prefix for thing name
    prefix = os.environ.get('THING_NAME_PREFIX', 'campo-vision-')
    
    # If device_id doesn't start with the prefix, add it
    if not device_id.startswith(prefix):
        client_id = f"{prefix}{device_id}"
    else:
        client_id = device_id
    
    # Initialize MQTT client
    mqtt_client = AWSIoTMQTTClient(client_id)
    mqtt_client.configureEndpoint(endpoint, 8883)
    mqtt_client.configureCredentials(
        str(root_ca_path),
        str(private_key_path),
        str(cert_path)
    )
    
    # Configure connection parameters
    mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
    mqtt_client.configureOfflinePublishQueueing(-1)  # Infinite queueing
    mqtt_client.configureDrainingFrequency(2)  # Draining: 2 Hz
    mqtt_client.configureConnectDisconnectTimeout(10)  # 10 seconds
    mqtt_client.configureMQTTOperationTimeout(5)  # 5 seconds
    
    return mqtt_client

def generate_telemetry_data(device_id):
    """
    Generate synthetic telemetry data for testing
    
    Args:
        device_id (str): Device ID
        
    Returns:
        dict: Telemetry data payload
    """
    # Generate random coordinates within a reasonable area
    # These are example coordinates for agricultural areas
    base_lat = random.uniform(30.0, 45.0)  # North America agricultural belt
    base_lon = random.uniform(-100.0, -80.0)
    
    # Add small random movement
    lat = base_lat + random.uniform(-0.01, 0.01)
    lon = base_lon + random.uniform(-0.01, 0.01)
    
    # Generate telemetry data with the same fields as the REST API
    # Including timestamp in ISO format with Z suffix
    telemetry = {
        "deviceId": device_id,
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "temperature": round(random.uniform(15.0, 35.0), 1),
        "speed": round(random.uniform(0, 15), 1),
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    
    return telemetry

def send_telemetry(mqtt_client, device_id, interval=5, count=None):
    """
    Send telemetry data at specified intervals
    
    Args:
        mqtt_client (AWSIoTMQTTClient): Configured MQTT client
        device_id (str): Device ID
        interval (int): Interval between messages in seconds
        count (int, optional): Number of messages to send, None for infinite
    """
    # Connect to AWS IoT Core
    logger.info(f"Connecting to AWS IoT Core...")
    mqtt_client.connect()
    logger.info("Connected!")
    
    # Topic to publish to
    topic = f"campo-vision/telemetry"
    
    # Remove prefix if present for the payload
    prefix = os.environ.get('THING_NAME_PREFIX', 'campo-vision-')
    if device_id.startswith(prefix):
        payload_device_id = device_id[len(prefix):]
    else:
        payload_device_id = device_id
    
    # Send telemetry data
    sent_count = 0
    try:
        while count is None or sent_count < count:
            # Generate telemetry data
            telemetry = generate_telemetry_data(payload_device_id)
            
            # Convert to JSON
            payload = json.dumps(telemetry)
            
            # Publish message
            logger.info(f"Publishing message {sent_count + 1}{'/' + str(count) if count else ''} to {topic}")
            logger.info(f"Payload: {payload}")
            
            mqtt_client.publish(topic, payload, 1)  # QoS 1
            
            sent_count += 1
            
            # Wait for the next interval
            if count is None or sent_count < count:
                logger.info(f"Waiting {interval} seconds before sending next message...")
                time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Disconnecting...")
    
    finally:
        # Disconnect
        mqtt_client.disconnect()
        logger.info(f"Disconnected. Sent {sent_count} messages.")
        
        # Provide a summary of what was done
        logger.info("\nSummary:")
        logger.info(f"- Sent {sent_count} telemetry messages to topic '{topic}'")
        logger.info(f"- Device ID: {payload_device_id}")
        logger.info(f"- Data format: Individual fields (deviceId, latitude, longitude, temperature, speed)")
        logger.info("\nCheck your DynamoDB table to verify the data format.")
        logger.info("The IoT Rule should have stored the data with individual fields rather than a nested JSON object.")


def main():
    parser = argparse.ArgumentParser(description='Send telemetry data to AWS IoT Core using MQTT')
    
    parser.add_argument('--device-id', required=True, help='Device ID to use for sending telemetry')
    parser.add_argument('--interval', type=int, default=5, help='Interval between messages in seconds (default: 5)')
    parser.add_argument('--count', type=int, help='Number of messages to send (default: infinite)')
    
    args = parser.parse_args()
    
    try:
        # Set up MQTT client
        mqtt_client = setup_mqtt_client(args.device_id)
        
        # Send telemetry data
        send_telemetry(mqtt_client, args.device_id, args.interval, args.count)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
