import os, time, boto3
REGION = os.getenv("AWS_REGION", "eu-central-1")
TABLE  = os.getenv("DDB_TABLE_NAME", "Reports")
ENDPOINT = os.getenv("AWS_DDB_ENDPOINT", "http://localhost:8001")  # host:port til DynamoDB Local

ddb = boto3.resource("dynamodb", region_name=REGION, endpoint_url=ENDPOINT)

def ensure_table():
    existing = [t.name for t in ddb.tables.all()]
    if TABLE in existing:
        print("Table already exists:", TABLE)
        return
    print("Creating table:", TABLE)
    ddb.create_table(
        TableName=TABLE,
        KeySchema=[
            {"AttributeName": "userId", "KeyType": "HASH"},
            {"AttributeName": "createdAt", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "userId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "N"},
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[{
            "IndexName": "byId",
            "KeySchema": [{"AttributeName":"id","KeyType":"HASH"}],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        }],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    ).wait_until_exists()
    print("Table created.")

if __name__ == "__main__":
    ensure_table()
