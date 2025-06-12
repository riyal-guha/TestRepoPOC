from azure.servicebus.aio import ServiceBusClient
import asyncio
from azure.servicebus import ServiceBusMessage
import json


CONNECTION_STR = "Endpoint=sb://localhost:5672;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"  
QUEUE_NAME = "queue.1" 
TOPIC_NAME = "topic.1"
SUBSCRIPTION_NAME = "subscription.2"

def create_test_payload():
    payload = {
    "messageId": "12345",
    "eventType": "ExecuteActionPlan",
    "timestamp": "2025-05-20T12:34:56Z",
    "data": {
        "flowId": "flowId123",
        "userId": "pnl0usXX",
        "nlp": "Go to amazon.com and search for macbook pro",
        "actionPlan": """1. Go to amazon.com
        2. Search for macbook pro.""",
        "overrideSystemPrompt": "You are an AI agent that helps users with web browsing tasks.",
            }
            }
    return payload

async def send_message(servicebus_client,payload):
    sender = servicebus_client.get_topic_sender(topic_name=TOPIC_NAME)
    message = ServiceBusMessage(
    json.dumps(payload),  # JSON body
    content_type="application/json",
    application_properties={
        "eventType": "ExecuteActionPlan",
    }
)
    await sender.send_messages(message)
    print("Message sent to Topic:", message)

async def main():
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)

    async with servicebus_client:
        payload = create_test_payload()
        await send_message(servicebus_client,payload)


if __name__ == "__main__":
    asyncio.run(main())


