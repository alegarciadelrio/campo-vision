import json
import os
import sys
sys.path.append('functions/get-telemetry')
import app

# Set environment variable for the table
os.environ['TELEMETRY_TABLE'] = 'TelemetryTable'

# Load test event
with open('events/get-event.json', 'r') as f:
    event = json.load(f)

# Invoke the Lambda handler
response = app.lambda_handler(event, None)

# Print the response
print(json.dumps(response, indent=2))
