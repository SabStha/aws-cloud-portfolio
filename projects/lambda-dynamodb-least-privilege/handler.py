import json
import os

import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def respond(status, body):
    return {"statusCode": status, "body": json.dumps(body, default=str)}


def lambda_handler(event, context):
    order_id = (event or {}).get("order_id")
    if not order_id:
        return respond(400, {"error": "order_id is required"})

    result = table.get_item(Key={"order_id": str(order_id)})
    item = result.get("Item")
    if item is None:
        return respond(404, {"error": f"order {order_id} not found"})
    return respond(200, item)
