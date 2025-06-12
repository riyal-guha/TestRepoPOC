# Install the Azure Service Bus SDK for Python using following command prior to running the sample. Versions >=7.14.0 support Emulator.
# pip install azure-servicebus==7.14.0 

from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
import json
import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()
from browser_use import Agent, BrowserSession
from datetime import datetime,timezone

CONNECTION_STR = "Endpoint=sb://localhost:5672;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"  
QUEUE_NAME = "queue.1" 
TOPIC_NAME = "topic.1"
SUBSCRIPTION_NAME = "subscription.2"

def process_action_plan(input_json):
    action_plan = input_json.get("data", {}).get("actionPlan", "")
    return action_plan

def process_override_system_message(input_json):
    override_system_message = input_json.get("data", {}).get("overrideSystemPrompt", "")
    return override_system_message

async def execute_agent_with_json(input_json):
    action_plan = process_action_plan(input_json)
    override_system_message = process_override_system_message(input_json)
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp')

    initial_actions = [
        {'open_tab': {'url': 'https://www.google.com'}},
    ]

    browser_session = BrowserSession(
        executable_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    )

    agent = Agent(
        task=action_plan,
        initial_actions=initial_actions,
        llm=llm,
        override_system_message=override_system_message,
        browser_session=browser_session,
        generate_gif=True,
        save_conversation_path="logs/conversation"
    )
    result = await agent.run()
    return result

def passinfo(payload, result):
    modified_payload = payload.copy()
    modified_payload['eventType'] = "ExecutionEngine"
    modified_payload['timestamp'] = datetime.now(timezone.utc).isoformat()
    modified_payload['data']['action_status'] = result.is_done()

    return modified_payload

def create_test_payload():
    payload = {
    "messageId": "12345",
    "eventType": "ExecuteActionPlan",
    "timestamp": "2025-05-20T12:34:56Z",
    "data": {
        "flowId": "flowId123",
        "userId": "pnl0usXX",
        "nlp": "Go to netflix.com and go to sign up page",
        "actionPlan": """1. Go to netflix.com
        2. Go to the sign up page."""
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

async def send_modified_payload(servicebus_client, updated_payload):
    sender = servicebus_client.get_topic_sender(topic_name=TOPIC_NAME)
    async with sender:
        message = ServiceBusMessage(
            json.dumps(updated_payload),
            content_type="application/json",
            application_properties={
                "eventType": "ExecutionEngine"
            }
        )
        await sender.send_messages(message)
        print("Modified payload sent back to topic.")

# async def receive_and_process_message(servicebus_client):
#         receiver = servicebus_client.get_subscription_receiver(
#             topic_name=TOPIC_NAME,
#             subscription_name=SUBSCRIPTION_NAME
#         )

#         async with receiver:
#             received_msgs = await receiver.receive_messages(max_message_count=1, max_wait_time=10)
#             for msg in received_msgs:
#                 payload = json.loads(str(msg))
#                 print("Received Payload:\n", json.dumps(payload, indent=2))

#                 result = await execute_agent_with_json(payload)

#                 # Print result and updated payload
#                 print("Execution Done:", result.is_done())
#                 updated_payload = passinfo(payload, result)
#                 print("Updated Payload:\n", json.dumps(updated_payload, indent=2))
#                 await receiver.complete_message(msg)
#                 await send_modified_payload(servicebus_client, updated_payload)



async def receive_and_process_message(servicebus_client):
        receiver = servicebus_client.get_subscription_receiver(
            topic_name=TOPIC_NAME,
            subscription_name=SUBSCRIPTION_NAME
        )

        async with receiver:
            # received_msgs = await receiver.receive_messages(max_message_count=1, max_wait_time=10)
            async for msg in receiver:
                body_bytes = b"".join([b for b in msg.body])
                body_str = body_bytes.decode("utf-8")
                payload = json.loads(body_str)
                print("Received Payload:\n", json.dumps(payload, indent=2))

                result = await execute_agent_with_json(payload)

                # Print result and updated payload
                print("Execution Done:", result.is_done())
                updated_payload = passinfo(payload, result)
                print("Updated Payload:\n", json.dumps(updated_payload, indent=2))
                await receiver.complete_message(msg)
                await send_modified_payload(servicebus_client, updated_payload)


# def receive_messages(receiver):
#     with receiver:
#         for msg in receiver.receive_messages(max_message_count=1, max_wait_time=5):
#             # print("Received messag from subscription:", str(msg))
#             json_payload = json.loads(str(msg))
#             print("Received message from subscription:", json.dumps(json_payload, indent=2))
#             receiver.complete_message(msg)

async def main():
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)

    async with servicebus_client:
        # payload = create_test_payload()
        # await send_message(servicebus_client,payload)

        # print("⏳ Waiting for message to propagate...")
        # await asyncio.sleep(2)  # brief wait to allow Service Bus to deliver the message

        await receive_and_process_message(servicebus_client)


if __name__ == "__main__":
    asyncio.run(main())