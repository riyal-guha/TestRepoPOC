import os
import datetime
import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage

def example_create_servicebus_client_async():
    # [START create_sb_client_from_conn_str_async]
    import os
    from azure.servicebus.aio import ServiceBusClient

    servicebus_connection_str = os.environ["SERVICEBUS_CONNECTION_STR"]
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=servicebus_connection_str)

    return servicebus_client

