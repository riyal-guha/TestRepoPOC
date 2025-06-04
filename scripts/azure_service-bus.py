# Install the Azure Service Bus SDK for Python using following command prior to running the sample. Versions >=7.14.0 support Emulator.
# pip install azure-servicebus==7.14.0 

from azure.servicebus import ServiceBusClient, ServiceBusMessage
import json

CONNECTION_STR = "Endpoint=sb://localhost;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"  
QUEUE_NAME = "queue.1" 
TOPIC_NAME = "topic.1"
SUBSCRIPTION_NAME = "subscription.2"

def send_message(sender):
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
    # message = ServiceBusMessage("This is a Sample Message To Test The Working of Topic")
    message = ServiceBusMessage(
    json.dumps(payload),  # JSON body
    content_type="application/json",
    application_properties={
        "eventType": "ExecuteActionPlan",
    }
)
    sender.send_messages(message)
    print("Message sent to Topic:", message)

def receive_messages(receiver):
    with receiver:
        for msg in receiver.receive_messages(max_message_count=1, max_wait_time=5):
            # print("Received messag from subscription:", str(msg))
            json_payload = json.loads(str(msg))
            print("Received message from subscription:", json.dumps(json_payload, indent=2))
            receiver.complete_message(msg)

def main():
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)

    with servicebus_client:
        # Sende messages to Queue
        # sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME)
        # with sender:
        #     send_message(sender)

        # Send Messages to Topic
        # sender = servicebus_client.get_topic_sender(topic_name=TOPIC_NAME)
        # with sender:
        #     send_message(sender)

        # Recieve messages from Queue
        # receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
        # with receiver:
        #     receive_messages(receiver)

        # Receive messages from Topic Subscription
        receiver = servicebus_client.get_subscription_receiver(
            topic_name=TOPIC_NAME,
            subscription_name=SUBSCRIPTION_NAME
        )
        with receiver:
            receive_messages(receiver)

if __name__ == "__main__":
    main()