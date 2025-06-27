from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
import json
import asyncio


CONNECTION_STR = "Endpoint=sb://localhost:5672;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"  
QUEUE_NAME = "queue.1" 
TOPIC_NAME = "status"
SUBSCRIPTION_NAME = "updates"

async def receive_message(servicebus_client):
        receiver = servicebus_client.get_subscription_receiver(
            topic_name=TOPIC_NAME,
            subscription_name=SUBSCRIPTION_NAME
        )

        async with receiver:
            received_msgs = await receiver.receive_messages(max_message_count=1, max_wait_time=10)
            for msg in received_msgs:
                payload = json.loads(str(msg))
                print("Received Payload:\n", json.dumps(payload, indent=2))
                await receiver.complete_message(msg)

async def main():
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)

    async with servicebus_client:
         await receive_message(servicebus_client)

if __name__ == "__main__":
    asyncio.run(main())