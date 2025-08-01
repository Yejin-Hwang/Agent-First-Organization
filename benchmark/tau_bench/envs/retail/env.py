from benchmark.tau_bench.envs.base import Env
from benchmark.tau_bench.envs.retail.data import load_data
from benchmark.tau_bench.envs.retail.rules import RULES
from benchmark.tau_bench.envs.retail.tools import ALL_TOOLS
from benchmark.tau_bench.envs.retail.wiki import WIKI
from benchmark.tau_bench.envs.user import UserStrategy


class MockRetailDomainEnv(Env):
    def __init__(
        self,
        user_strategy: str | UserStrategy = UserStrategy.LLM,
        user_model: str = "gpt-4o",
        user_provider: str | None = None,
        task_split: str = "test",
        task_index: int | None = None,
    ) -> None:
        match task_split:
            case "test":
                from benchmark.tau_bench.envs.retail.tasks_test import (
                    TASKS_TEST as tasks,
                )
            case "train":
                from benchmark.tau_bench.envs.retail.tasks_train import (
                    TASKS_TRAIN as tasks,
                )
            case "dev":
                from benchmark.tau_bench.envs.retail.tasks_dev import TASKS_DEV as tasks
            case _:
                raise ValueError(f"Unknown task split: {task_split}")
        super().__init__(
            data_load_func=load_data,
            tools=ALL_TOOLS,
            tasks=tasks,
            wiki=WIKI,
            rules=RULES,
            user_strategy=user_strategy,
            user_model=user_model,
            user_provider=user_provider,
            task_index=task_index,
        )
        self.terminate_tools = ["transfer_to_human_agents"]
