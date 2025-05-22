import boto3
import time

def create_table():
    # Create a DynamoDB client that connects to the local instance
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
    
    # Create the TelemetryTable
    table = dynamodb.create_table(
        TableName='TelemetryTable',
        KeySchema=[
            {'AttributeName': 'deviceId', 'KeyType': 'HASH'},  # Partition key
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'deviceId', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'TimestampIndex',
                'KeySchema': [
                    {'AttributeName': 'timestamp', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            }
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    
    # Wait for the table to be created
    print(f"Creating table {table.name}...")
    table.meta.client.get_waiter('table_exists').wait(TableName='TelemetryTable')
    print(f"Table {table.name} created successfully!")
    
    return table

if __name__ == '__main__':
    try:
        table = create_table()
        print(f"Table status: {table.table_status}")
    except Exception as e:
        print(f"Error creating table: {str(e)}")
