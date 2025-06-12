import json
import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()
from browser_use import Agent, BrowserSession
from datetime import datetime,timezone

def process_action_plan(input_json):
    action_plan = input_json.get("data", {}).get("actionPlan", "")
    return action_plan

def process_override_system_message(input_json):
    override_system_message = input_json.get("data", {}).get("overrideSystemPrompt", "")
    return override_system_message

def process_extend_system_message(input_json):
    extend_system_message = input_json.get("data", {}).get("extendSystemPrompt", "")
    return extend_system_message

async def execute_agent_with_json(input_json):
    action_plan = process_action_plan(input_json)
    override_system_message = process_override_system_message(input_json)
    extend_system_message = process_extend_system_message(input_json)
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
        override_system_message=override_system_message,
        extend_system_message=extend_system_message,
        browser_session=browser_session,  # Set to True to generate GIFs
        generate_gif=True,
        save_conversation_path="logs/conversation"  # Set to True to generate screenshots
    )
    result = await agent.run()
    return result

def passinfo(payload,result):
    modified_payload = payload.copy()
    modified_payload['eventType'] = "ExecutionEngine"
    modified_payload['timestamp'] = datetime.now(timezone.utc).isoformat()
    modified_payload['data']['action_status'] = result.is_done()
    return modified_payload

async def main():
    payload = {
        "messageId": "12345",
        "eventType": "CreateActionPlan",
        "timestamp": "2025-05-20T12:34:56Z",
        "data": {
            "flowId": "flowId123",
            "userId": "pnl0usXX",
            "nlp": "Go to netflix.com and go to sign up page",
            "actionPlan": """1.Go to netflix.com
            2. Go to the sign up page.
            3. End of Task.
            """,
            "overrideSystemPrompt": "You are an AI agent that helps users with web browsing tasks.",
            "extendSystemPrompt": "Remember an important rule: Always open a new tab and then follow the task to be executed",
        }
    }

    print(json.dumps(payload, indent=2))
    
    result = await execute_agent_with_json(payload)
    # print(result.screenshots())
    # print(result.action_names())
    # print(result.extracted_content())
    # print(result.model_actions())
    print(result.is_done())
    print(json.dumps(passinfo(payload, result), indent=2))

asyncio.run(main())
