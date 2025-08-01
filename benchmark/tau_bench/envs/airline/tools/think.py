from typing import Any

from benchmark.tau_bench.envs.tool import Tool


class Think(Tool):
    @staticmethod
    def invoke(data: dict[str, Any], thought: str) -> str:
        return ""

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "think",
                "description": "Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning is needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thought": {
                            "type": "string",
                            "description": "A thought to think about.",
                        },
                    },
                    "required": ["thought"],
                },
            },
        }
