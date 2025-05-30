import json
import asyncio
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
from browser_use import Agent
# data = {
#     "messageId": "12345",
#     "eventType": "CreateActionPlan",
#     "timestamp": "2025-05-20T12:34:56Z",
#     "data": {
#         "flowId": "flowId123",
#         "userId": "pnl0usXX",
#         "nlp": "Login to SNOW and view all tickets in all status",
#         "actionPlan": """Open https://aholddelhaize.service-now.com/
# Login with user pnl0us72 and password xxxxxxxxx
# View all tickets in all status
# logout"""
#     }
# }

# print(json.dumps(data, indent=2))

def process_action_plan(input_json):
    action_plan = input_json.get("data", {}).get("actionPlan", "")
    return action_plan

async def execute_agent_with_json(input_json):
    action_plan = process_action_plan(input_json)
    llm = ChatOpenAI(model='gpt-4o',
                     temperature=0.0,)
    agent = Agent(
        task=action_plan,
        llm=llm,
    )
    result = await agent.run()
    return result

async def main():
    payload = {
        "messageId": "12345",
        "eventType": "CreateActionPlan",
        "timestamp": "2025-05-20T12:34:56Z",
        "data": {
            "flowId": "flowId123",
            "userId": "pnl0usXX",
            "nlp": "Go to amazon and search",
            "actionPlan": """Go to amazon.com and search for macbook pro
            then close the browser"""
        }
    }

    print(json.dumps(payload, indent=2))
    
    result = await execute_agent_with_json(payload)
    print(result)

asyncio.run(main())