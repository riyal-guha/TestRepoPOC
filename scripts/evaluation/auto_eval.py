import time
from typing import TYPE_CHECKING
import re
from browser_use import AgentHistoryList
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI

if TYPE_CHECKING:
    from run_browser_use import EvalResult


SYSTEM_PROMPT = """
-- You DO NOT NEED to interact with web pages or perform actions such as booking flights or conducting searches on websites.
-- You SHOULD NOT make assumptions based on information not presented in the screenshot when comparing it to the instructions. If you cannot find any information in the screenshot that matches the instruction, you can believe the information in the response.
-- Your primary responsibility is to conduct a thorough assessment of the web task instruction against the outcome depicted in the screenshot and in the response, evaluating whether the actions taken align with the given instructions.
-- NOTE that the instruction may involve more than one task, for example, locating the garage and summarizing the review. Failing to complete either task, such as not providing a summary, should be considered unsuccessful.
-- NOTE that the screenshot is authentic, but the response provided by LLM is generated at the end of web browsing, and there may be discrepancies between the text and the screenshots.
-- Note the difference: 1) Result response may contradict the screenshot, then the content of the screenshot prevails, 2) The content in the Result response is not mentioned on the screenshot, choose to believe the content.
-- If you are not sure whether you should believe the content in the response, you should choose unknown.
You will be shown a web automation task and the output of two AI agents trying to complete that task.

For **each agent**, evaluate:
1. How well the agent followed the task instruction.
2. If the final textual result matches the task.
3. Whether screenshots support that the task was executed correctly.
4. Provide a **verdict**: SUCCESS / NOT SUCCESS / UNKNOWN.
5. Provide a **confidence score (0-100)** for each agent.

Format your response like this:

Agent 1:
- Evaluation: ...
- Verdict: ...
- Confidence Score: ...

Agent 2:
- Evaluation: ...
- Verdict: ...
- Confidence Score: ...

Only use screenshots and textual output to make your judgment. Prefer screenshots if there’s a conflict. If unsure, mark as UNKNOWN.
"""


USER_PROMPT_TEMPLATE = """TASK: <task>

Agent 1 Result:
<result1>

Agent 2 Result:
<result2>

Screenshots from Agent 1:
<agent1_screenshots>

Screenshots from Agent 2:
<agent2_screenshots>

Please evaluate each agent independently.
"""


def extract_verdict_and_score(response: str, agent_number: int) -> tuple[str, float]:
    verdict_match = re.search(rf"Agent {agent_number}.*?Verdict\s*[:\-]?\s*(SUCCESS|NOT SUCCESS|UNKNOWN)", response, re.IGNORECASE | re.DOTALL)
    score_match = re.search(rf"Agent {agent_number}.*?Confidence\s*Score\s*[:\-]?\s*(\d+)", response, re.IGNORECASE | re.DOTALL)

    verdict = "unknown"
    score = 0.0

    if verdict_match:
        v = verdict_match.group(1).upper()
        if "SUCCESS" in v:
            verdict = "success" if v == "SUCCESS" else "failed" if v == "NOT SUCCESS" else "unknown"

    if score_match:
        try:
            score = float(score_match.group(1))
            score = max(0.0, min(100.0, score))
        except ValueError:
            score = 0.0

    return verdict, score


async def auto_eval_by_gpt4o(
    task: str,
    history1: AgentHistoryList,
    history2: AgentHistoryList,
    openai_client: AzureChatOpenAI | ChatAnthropic | ChatGoogleGenerativeAI,
) -> tuple[str, str, float, str, float]:
    if not history1.is_done() or not history2.is_done():
        return "failed", "", 0.0, "failed", 0.0

    answer1 = history1.final_result() or "<NO FINAL RESULT>"
    answer2 = history2.final_result() or "<NO FINAL RESULT>"

    screenshots1 = history1.screenshots()[-3:]
    screenshots2 = history2.screenshots()[-3:]

    agent1_images = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{s}"}} for s in screenshots1
    ]
    agent2_images = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{s}"}} for s in screenshots2
    ]

    user_prompt = USER_PROMPT_TEMPLATE.replace("<task>", task)
    user_prompt = user_prompt.replace("<result1>", answer1)
    user_prompt = user_prompt.replace("<result2>", answer2)
    user_prompt = user_prompt.replace("<agent1_screenshots>", f"{len(screenshots1)} screenshots")
    user_prompt = user_prompt.replace("<agent2_screenshots>", f"{len(screenshots2)} screenshots")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=[
                {"type": "text", "text": user_prompt},
                *agent1_images,
                *agent2_images,
                {"type": "text", "text": "Please provide your evaluation."},
            ]
        ),
    ]

    while True:
        try:
            response = await openai_client.ainvoke(messages)
            break
        except Exception as e:
            print(f"Retrying after error: {e}")
            time.sleep(10)

    response_text = str(response.content)

    verdict1, score1 = extract_verdict_and_score(response_text, agent_number=1)
    verdict2, score2 = extract_verdict_and_score(response_text, agent_number=2)

    return verdict1, response_text, score1, verdict2, score2