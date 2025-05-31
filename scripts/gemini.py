import json
import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()
from browser_use import Agent, BrowserSession
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright

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
    headless = True,
    chromium_sandbox = False
    )
    agent = Agent(
        task=action_plan,
        initial_actions=initial_actions,
        llm=llm,
        browser_session=browser_session,  # Set to True to generate GIFs
        generate_gif=True,
        save_conversation_path="logs/conversation"  # Set to True to generate screenshots
    )
    # with async_playwright() as p:
        # browser = p.chromium.launch(headless=True)
        # page = browser.new_page()
        # page.goto("https://www.google.com")
        # result = await agent.run()
    # return result

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
            "nlp": "Go to amazon.com and search",
            "actionPlan": """Go to amazon.com and search for macbook pro
            """
        }
    }

    # print(json.dumps(payload, indent=2))
    
    # result = await execute_agent_with_json(payload)
    # print(result.screenshots())
    # print(result.action_names())
    # print(result.extracted_content())
    # print(result.model_actions())
    # print(result.is_done())
    # print(json.dumps(passinfo(payload, result), indent=2))

# from playwright.sync_api import sync_playwright

def search_google(query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100 Safari/537.36")
        page = context.new_page()

        print("Opening Google...")
        page.goto("https://www.google.com", timeout=60000)

        # Accept cookies if the consent form appears (EU regions)
        try:
            page.locator('button:has-text("Accept all")').click(timeout=5000)
        except:
            pass  # Skip if not present

        print("Waiting for search box...")
        page.wait_for_selector('input[name="q"]', timeout=10000)
        page.fill('input[name="q"]', query)
        page.keyboard.press("Enter")

        print("Waiting for results...")
        page.wait_for_selector("h3", timeout=10000)
        top_result = page.locator("h3").first.text_content()

        print(f"Top result for '{query}': {top_result}")
        browser.close()

search_google("OpenAI GPT-4")


# asyncio.run(main())