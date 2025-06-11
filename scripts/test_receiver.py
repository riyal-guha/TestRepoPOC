from azure.servicebus.aio import ServiceBusClient
import json
import asyncio

async def receive_message(conn_str, topic_name, subscription_name):
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=conn_str, logging_enable=True)
    
    async with servicebus_client:
        receiver = servicebus_client.get_subscription_receiver(
            topic_name=topic_name,
            subscription_name=subscription_name
        )
        async with receiver:
            async for message in receiver:
                    body_bytes = b"".join([b for b in message.body])
                    body_str = body_bytes.decode("utf-8")
                    data = json.loads(body_str)
                    print("Received JSON:", data)
                    await receiver.complete_message(message)


if __name__ == "__main__":
    CONNECTION_STR =  "Endpoint=sb://localhost:5672;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"
    TOPIC_NAME = "topic.1"
    SUBSCRIPTION_NAME = "subscription.2"

    asyncio.run(receive_message(CONNECTION_STR, TOPIC_NAME, SUBSCRIPTION_NAME))