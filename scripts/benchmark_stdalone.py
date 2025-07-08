import argparse
import asyncio
import json
import logging
import os
import random
import shutil
from asyncio import Semaphore
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Literal, Set, TypedDict

from browser_use import Agent, BrowserSession, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field, SecretStr
from browser_use.agent.views import AgentHistoryList


from evaluation.auto_eval import auto_eval_by_gpt4o

load_dotenv()


class TaskData(TypedDict):
    flowId: str
    userId: str
    nlp: str
    actionPlan: str
    overrideSystemPrompt: str = ""
    extendSystemPrompt: str = ""


EvalResult = Literal["success", "failed", "unknown"]


@dataclass
class RunStats:
    total_tasks: int
    current_task: int = 0
    successful_tasks: Set[str] = field(default_factory=set)
    failed_tasks: Set[str] = field(default_factory=set)
    unknown_tasks: Set[str] = field(default_factory=set)

    def update(self, task_id: str, success: "EvalResult") -> None:
        if success == "success":
            self.successful_tasks.add(task_id)
        elif success == "failed":
            self.failed_tasks.add(task_id)
        else:
            self.unknown_tasks.add(task_id)

    def get_success_rate(self) -> str:
        if self.current_task == 0:
            return "0/0=0.00"
        return f"{len(self.successful_tasks)}/{self.current_task}={len(self.successful_tasks) / self.current_task:.2f}"

    def print_periodic_summary(self) -> None:
        print("\n=== Task Summary ===")
        print(
            f"Successful tasks ({len(self.successful_tasks)}): {sorted(list(self.successful_tasks))}"
        )
        print(
            f"Failed tasks ({len(self.failed_tasks)}): {sorted(list(self.failed_tasks))}"
        )
        print(f"Current success rate: {self.get_success_rate()}")
        print("==================\n")


class TaskResult(BaseModel):
    task_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    num_steps_agent1: int
    num_steps_agent2: int
    verdict_agent1: EvalResult
    verdict_agent2: EvalResult
    score_agent1: float
    score_agent2: float
    task_prompt: str
    final_answer_agent1: str
    final_answer_agent2: str
    gpt_4v_res: str


class ExperimentResults(BaseModel):
    total_tasks: int = 0
    total_success: int = 0
    total_failed: int = 0
    total_unknown: int = 0
    all_tasks: List[TaskResult] = Field(default_factory=list)


def cleanup_webdriver_cache() -> None:
    """Clean up webdriver cache directories."""
    cache_paths = [
        Path.home() / ".wdm",
        Path.home() / ".cache" / "selenium",
        Path.home() / "Library" / "Caches" / "selenium",
    ]
    for path in cache_paths:
        if path.exists():
            print(f"Removing cache directory: {path}")
            shutil.rmtree(path, ignore_errors=True)


def create_task_result(
    task: TaskData,
    start_time: datetime,
    verdict1: EvalResult,
    verdict2: EvalResult,
    score1: float,
    score2: float,
    num_steps_1: int,
    num_steps_2: int,
    final_answer_1: str,
    final_answer_2: str,
    gpt_4v_res: str,
) -> TaskResult:
    end_time = datetime.now()
    return TaskResult(
        task_id=task["flowId"],
        start_time=start_time,
        end_time=end_time,
        duration_seconds=(end_time - start_time).total_seconds(),
        num_steps_agent1=num_steps_1,
        num_steps_agent2=num_steps_2,
        verdict_agent1=verdict1,
        verdict_agent2=verdict2,
        score_agent1=score1,
        score_agent2=score2,
        task_prompt=task["actionPlan"],
        final_answer_agent1=final_answer_1,
        final_answer_agent2=final_answer_2,
        gpt_4v_res=gpt_4v_res,
    )


def save_results(
    task_result: TaskResult,
    task_dir: Path,
) -> None:
    """Save results to files."""
    # Save interaction messages

    with open(task_dir / "task_result.json", "w") as f:
        json.dump(task_result.model_dump(), f, indent=2, default=str)


def print_task_progress(
    task_id: str, steps: int, success: EvalResult, stats: RunStats
) -> None:
    """Print concise task progress."""
    status = "✓" if success == "success" else "✗" if success == "failed" else "?"
    print(
        f"Task {task_id} [{stats.current_task}/{stats.total_tasks}] "
        f"Steps: {steps} Status: {status} Score: {stats.get_success_rate()}"
    )


def save_experiment_results(experiment_results: ExperimentResults) -> None:
    """Save experiment results to file."""
    with open("./results/examples-browser-use/experiment_results.json", "w") as f:
        json.dump(experiment_results.model_dump(), f, indent=2, default=str)


@dataclass
class LLMModel:
    model: AzureChatOpenAI
    token_limit: int


def get_llm_model_generator(
    model_provider: str,
) -> Generator[AzureChatOpenAI | ChatAnthropic, None, None]:
    """Generator that creates fresh model instances each time"""
    while True:
        # Force reload environment variables
        load_dotenv(override=True)

        if model_provider == "azure":
            # Create fresh instances each time, reading current env vars
            west_eu = LLMModel(
                model=AzureChatOpenAI(
                    model="gpt-4o",
                    api_version="2024-10-21",
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_WEST_EU", ""),
                    api_key=SecretStr(os.getenv("AZURE_OPENAI_API_KEY_WEST_EU", "")),
                ),
                token_limit=900,
            )
            yield west_eu.model

        elif model_provider == "google/gemini-1.5-flash":
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
            )
            yield llm

        else:
            raise ValueError(f"Invalid model provider: {model_provider}")


async def process_single_task(
    task: TaskData,
    client: AzureChatOpenAI | ChatAnthropic,
    stats: RunStats,
    results_dir: Path,
    experiment_results: ExperimentResults,
    browser: BrowserSession,
    history1: AgentHistoryList,
    history2: AgentHistoryList,
) -> None:
    """Process a single task asynchronously."""
    task_str = f"{task['actionPlan']}"
    task_id = task.get("flowId")
    start_time = datetime.now()
    task_dir = results_dir / task_id
    task_dir.mkdir(exist_ok=True)

    try:
        if not (task_dir / "task_result.json").exists():
            logging.getLogger("browser_use").setLevel(logging.INFO)

            # await browser.start()
            # agent = Agent(
            #     task=task_str,
            #     llm=client,
            #     browser_session=browser,
            #     validate_output=True,
            #     generate_gif=False,
            # )

            # history = await agent.run(max_steps=15)
            # history.save_to_file(task_dir / "history.json")

            verdict1, gpt_4v_res, score1, verdict2, score2 = await auto_eval_by_gpt4o(
                task=task["actionPlan"],
                history1=history1,
                history2=history2,
                openai_client=client,
            )
######################## needs to be checked from here##############################################################
            task_result = create_task_result(
                task=task,
                start_time=start_time,
                verdict1=verdict1,
                verdict2=verdict2,
                score1=score1,
                score2=score2,
                num_steps_1=len(history1.history),
                num_steps_2=len(history2.history),
                final_answer_1=history1.final_result() or "<NO FINAL>",
                final_answer_2=history2.final_result() or "<NO FINAL>",
                gpt_4v_res=gpt_4v_res,
            )
            save_results(task_result, task_dir)
        else:
            task_result = TaskResult(**json.load(open(task_dir / "task_result.json")))
            verdict1 = task_result.verdict_agent1

        stats.update(task["flowId"], verdict1)
        print_task_progress(task["flowId"], task_result.num_steps_agent1, verdict1, stats)

        # Update experiment results
        experiment_results.all_tasks.append(task_result)
        experiment_results.total_tasks += 1
        experiment_results.total_success += int(verdict1 == "success")
        experiment_results.total_failed += int(verdict1 == "failed")
        experiment_results.total_unknown += int(verdict1 == "unknown")

        print(f"Saving stats to file {stats.current_task} {stats.get_success_rate()}")
        # with open(file="results/examples-browser-use/aaa_stats.txt", mode="a") as f:
        #     # in one line
        #     f.write(f"{stats.current_task}\n")
        #     f.write(f"{stats.get_success_rate()}\n")

    except Exception as e:
        logging.error(f"Error processing task {task['flowId']}: {str(e)}")
        stats.update(task["flowId"], "failed")
    finally:
        await browser.close()


async def benchmark(result1: AgentHistoryList,result2: AgentHistoryList,single_task: dict,max_concurrent_tasks: int, model_provider: str) -> None:
    try:
        # Setup
        cleanup_webdriver_cache()
        semaphore = Semaphore(max_concurrent_tasks)

        # Load tasks
        tasks: List[TaskData] = [single_task]
        # with open("./data/WebVoyager_data.jsonl", "r") as f:
        #     for line in f:
        #         tasks.append(json.loads(line))

        # # remove impossible tasks
        # with open("data/WebVoyagerImpossibleTasks.json", "r") as f:
        #     impossible_tasks = set(json.load(f))
        # tasks = [task for task in tasks if task["id"] not in impossible_tasks]

        # randomize the order of tasks
        # random.seed(42)
        # random.shuffle(tasks)

        # Initialize

        experiment_results = ExperimentResults()
        stats = RunStats(total_tasks=len(tasks))
        results_dir = Path("./results/examples-browser-use")
        results_dir.mkdir(parents=True, exist_ok=True)

        # Process tasks concurrently with semaphore
        async def process_with_semaphore(
            task: TaskData, client: AzureChatOpenAI | ChatAnthropic,history1: AgentHistoryList,history2: AgentHistoryList
        ) -> None:
            async with semaphore:
                print(f"\n=== Now at task {task['flowId']} ===")

                # Create browser instance inside the semaphore block
                # browser = Browser(
                #     config=BrowserConfig(
                #         headless=True,
                #         disable_security=True,
                #         new_context_config=BrowserContextConfig(
                #             disable_security=True,
                #             wait_for_network_idle_page_load_time=5,
                #             maximum_wait_page_load_time=20,
                #             # no_viewport=True,
                #             browser_window_size={
                #                 "width": 1280,
                #                 "height": 1100,
                #             },
                #             # trace_path=str(results_dir / f"{task['id']}"),
                #         ),
                #     )
                # )
                browser_session = BrowserSession(
                headless=True,
                disable_security=True,
                wait_for_network_idle_page_load_time=5,
                maximum_wait_page_load_time=20,
                viewport={"width": 1280, "height": 1100},
                
                # trace_path=str(results_dir / task_id)  # Only if using tracing
                )

                await process_single_task(
                    task,
                    client,
                    stats,
                    results_dir,
                    experiment_results,
                    browser_session,
                    history1,
                    history2 # Pass browser instance
                )
                stats.current_task += 1

                # Add this to ensure browser is always closed
                try:
                    await browser_session.close()
                except Exception as e:
                    logging.error(f"Error closing browser: {e}")

                print(f"Current task: {stats.current_task}")
                print(f"Total tasks: {stats.total_tasks}")
                print(f"Success rate: {stats.get_success_rate()}")
                # if stats.current_task % max_concurrent_tasks == 0:
                stats.print_periodic_summary()
                save_experiment_results(experiment_results)

        # Create and run all tasks
        # all_tasks = []
        # for i, task in enumerate(tasks):
        model = next(get_llm_model_generator(model_provider))
        await process_with_semaphore(single_task, model,result1,result2)

        # Add timeout and better error handling
        # await asyncio.gather(*all_tasks, return_exceptions=True)
    except Exception as e:
        logging.error(f"Benchmark loop error: {e}")
    finally:
        # Cleanup code here
        logging.info("Shutting down...")
        stats.print_periodic_summary()
