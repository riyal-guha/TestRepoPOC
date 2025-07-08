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
You are an expert web task evaluator.

Your job is to compare the performance of two agents that attempted to complete a browser-based task.

You will be provided:
- The original user task
- The final answers given by both agents
- The step-by-step history of each agent
- A few representative screenshots captured during execution

For each agent, assess how successfully it completed the task on a scale of 0 to 100, where 0 means total failure and 100 means perfect execution.

Provide:
- A brief evaluation
- A final verdict: success / failed / unknown
- A numerical success score (0–100)

Respond in the format:
Agent 1:
- Verdict: success | failed | unknown
- Score: <your score>
- Evaluation: <your comments>

Agent 2:
- Verdict: success | failed | unknown
- Score: <your score>
- Evaluation: <your comments>

- Prefer screenshot evidence when there’s a contradiction between screenshots and final answers.

"""


USER_PROMPT_TEMPLATE = """
User task: {task}

Agent 1 final answer: {answer1}
Agent 1 steps:
{steps1}
Agent 1 screenshots:
{screenshots1}

Agent 2 final answer: {answer2}
Agent 2 steps:
{steps2}
Agent 2 screenshots:
{screenshots2}
"""


def extract_verdict_and_score(response: str, agent_number: int) -> tuple[str, float]:
    verdict_match = re.search(rf"Agent {agent_number}.*?Verdict\s*[:\-]?\s*(success|failed|unknown)", response, re.IGNORECASE | re.DOTALL)
    score_match = re.search(rf"Agent {agent_number}.*?Score\s*[:\-]?\s*(\d+)", response, re.IGNORECASE | re.DOTALL)

    verdict = "unknown"
    score = 0.0

    if verdict_match:
        verdict = verdict_match.group(1).lower()

    if score_match:
        try:
            score = float(score_match.group(1))
            score = max(0.0, min(100.0, score))
        except ValueError:
            score = 0.0

    return verdict, score


def history_to_text(history: AgentHistoryList) -> str:
    lines = []
    thoughts = history.model_thoughts()
    actions = history.model_actions()
    results = history.action_results()
    urls = history.urls()

    for i in range(history.number_of_steps()):
        step = [f"Step {i + 1}:"]
        
        if i < len(thoughts):
            step.append(f"- Thought: {thoughts[i]}")
        
        if i < len(actions):
            action_dict = actions[i]
            action_type = list(action_dict.keys())[0] if action_dict else "unknown"
            step.append(f"- Action: {action_type} - {action_dict}")
        
        if i < len(urls):
            step.append(f"- URL: {urls[i] or 'N/A'}")
        
        if i < len(results):
            if results[i].extracted_content:
                step.append(f"- Extracted: {results[i].extracted_content}")
            if results[i].error:
                step.append(f"- Error: {results[i].error}")

        lines.append("\n".join(step))
    
    return "\n\n".join(lines)



async def auto_eval_by_gpt4o(
    task: str,
    history1: AgentHistoryList,
    history2: AgentHistoryList,
    openai_client: AzureChatOpenAI | ChatAnthropic | ChatGoogleGenerativeAI,
) -> tuple[str, str, float, str, float]:
    if not history1.is_done() or not history2.is_done():
        return "failed", "", 0.0, "failed", 0.0

    final1 = history1.final_result() or "<NO FINAL RESULT>"
    final2 = history2.final_result() or "<NO FINAL RESULT>"
    steps1 = history_to_text(history1)
    steps2 = history_to_text(history2)
    screenshots1 = history1.screenshots()[-4:]
    screenshots2 = history2.screenshots()[-4:]

    agent1_images = [
        {"type": "text", "text": "Screenshots from Agent 1:"},
        *[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}} for img in screenshots1],
    ]
    agent2_images = [
        {"type": "text", "text": "Screenshots from Agent 2:"},
        *[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}} for img in screenshots2],
    ]

    user_prompt = USER_PROMPT_TEMPLATE.format(
        task=task,
        answer1=final1,
        steps1=steps1,
        screenshots1=f"{len(screenshots1)} screenshots",
        answer2=final2,
        steps2=steps2,
        screenshots2=f"{len(screenshots2)} screenshots",
    )

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