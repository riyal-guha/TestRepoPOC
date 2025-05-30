import json
import asyncio
import os
from langchain_openai import ChatOpenAI

from browser_use import Agent
data = {
    "messageId": "12345",
    "eventType": "CreateActionPlan",
    "timestamp": "2025-05-20T12:34:56Z",
    "data": {
        "flowId": "flowId123",
        "userId": "pnl0usXX",
        "nlp": "Login to SNOW and view all tickets in all status",
        "actionPlan": """Open https://aholddelhaize.service-now.com/
Login with user pnl0us72 and password xxxxxxxxx
View all tickets in all status
logout"""
    }
}
print(json.dumps(data, indent=2))
print(os.environ['OPENAI_API_KEY'])
llm = ChatOpenAI(
	model='gpt-4o',
	temperature=0.0,
	api_key=os.environ['OPENAI_API_KEY'],
)
task = 'Go to amazon.com, search for laptop'
agent = Agent(task=task, llm=llm)

async def main():
	await agent.run()


if __name__ == '__main__':
	asyncio.run(main())