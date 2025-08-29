import json
import boto3
import os
from boto3.dynamodb.conditions import Attr


def handler(event, context):

    dynamodb = boto3.resource("dynamodb")

    log_level = os.environ.get("LOG_LEVEL", "ERROR").upper()

    # Zones are not referenced in other FACTS, so, nothing to do yet

    try:
        count = 0
        for record in event["Records"]:
            if record["eventName"] == "REMOVE":
                portfolio_facts = record["dynamodb"]["OldImage"]["ClientPortfolio"]["S"]
                zone = record["dynamodb"]["OldImage"]["Zone"]["S"]

                count += 1
                if log_level == "INFO":
                    print(f"SUCCESS: [{portfolio_facts}], zone: [{zone}] deleted")

        print(f"SUCCESS: {count} records deleted")

        return {"statusCode": 200, "body": json.dumps(f"Success: {count} records deleted")}

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
