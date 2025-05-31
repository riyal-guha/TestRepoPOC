import json
import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()
from browser_use import Agent, BrowserSession

def process_action_plan(input_json):
    action_plan = input_json.get("data", {}).get("actionPlan", "")
    return action_plan

async def execute_agent_with_json(input_json):
    action_plan = process_action_plan(input_json)
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp')
    initial_actions = [
	{'open_tab': {'url': 'https://www.google.com'}},
]
    browser_session = BrowserSession(
    # Path to a specific Chromium-based executable (optional)
    executable_path='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    # user_data_dir='~/.config/browseruse/profiles/default',   # this is the default
)
    agent = Agent(
        task=action_plan,
        initial_actions=initial_actions,
        llm=llm,
        browser_session=browser_session,
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
            "nlp": "Go to amazon.com and search",
            "actionPlan": """Go to amazon.com and search for macbook pro
            then close the tab"""
        }
    }

    print(json.dumps(payload, indent=2))
    
    result = await execute_agent_with_json(payload)
    print(result.final_result())

asyncio.run(main())