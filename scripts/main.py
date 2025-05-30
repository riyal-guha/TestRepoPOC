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
# ap_key = os.environ['OPENAI_API_KEY']
# print(ap_key)

llm = ChatOpenAI(
	model='gpt-4o',
	temperature=0.0,
	api_key="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",
)
task = 'Go to amazon.com, search for laptop'
agent = Agent(task=task, llm=llm)

async def main():
	await agent.run()


if __name__ == '__main__':
	asyncio.run(main())