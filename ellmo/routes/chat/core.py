import json
from typing import List
from openai import OpenAI, NotGiven

from ellmo.internal.models import ChatCompletionRequest, ChatCompletionResponse
from ellmo.routes.chat.content_generator import ContentGenerator


class PromptExecutor:
    def __init__(self, open_api_key: str, max_results: int):
        self.client = OpenAI(api_key=open_api_key)
        self.content_generator = ContentGenerator(max_results=max_results)

    def _get_messages_response(
        self,
        prompt_request: ChatCompletionRequest,
        messages: list[dict],
        tool_calls: list[dict] = None,
    ) -> ChatCompletionResponse:
        return self.client.chat.completions.create(
            model=prompt_request.model,
            messages=messages,
            max_completion_tokens=prompt_request.max_completion_tokens,
            temperature=prompt_request.temperature,
            tools=tool_calls,
        )

    def _prep_prompt(
        self, prompt_request: ChatCompletionRequest
    ) -> tuple[List[dict], List[dict]]:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_content",
                    "description": "Get additional fresh content from the internet. Call this whenever you need to know fresh data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_queries": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "top_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "refined_prompt": {"type": "string"},
                        },
                        "required": [
                            "search_queries",
                            "top_keywords",
                            "refined_prompt",
                        ],
                        "additionalProperties": False,
                    },
                },
            }
        ]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful research assistant that returns topics to research. "
                    "For 'top_keywords', return a list of the top 5"
                    " keywords that describe the topic. For 'search_queries', "
                    "provide 1-3 search queries that would be relevant for finding more "
                    "information on the topic. For 'refined_prompt', return a "
                    "prompt that includes the original prompt with additional points to highlight."
                ),
            },
            *[
                {"role": message.role, "content": message.content}
                for message in prompt_request.messages
            ],
        ]

        return (messages, tools)

    def _prep_rag_prompt(
        self, content_results: list[dict], query: str, tool_call_id: str
    ) -> list[dict]:
        context_prompt = (
            "You are a helpful AI assistant with access to fresh data past your training data - It is included here"
            "- Use the provided context information to add additional information"
            "- If the context does not cover the query, acknowledge that"
            "- Cite the sources (use the URL value of the associated document) of information when possible"
        )

        for content in content_results:
            context_prompt += "\n".join(f"{k}: {v}" for k, v in content.items())
            context_prompt += "\n"

        context_prompt += f"Based on the information above, please answer: {query}"

        return {"role": "tool", "content": context_prompt, "tool_call_id": tool_call_id}

    def _execute_tool_call(
        self,
        search_queries: list[str],
        top_keywords: list[str],
        refined_prompt: str,
        tool_call_id: str,
    ) -> list[dict]:
        content_results = self.content_generator.get_content(
            search_queries, top_keywords
        )
        return self._prep_rag_prompt(content_results, refined_prompt, tool_call_id)

    def execute(self, prompt_request: ChatCompletionRequest) -> ChatCompletionResponse:
        messages, tools = self._prep_prompt(prompt_request)
        base_response = self._get_messages_response(prompt_request, messages, tools)

        if not base_response.choices[0].message.tool_calls:
            return base_response

        tool_call = base_response.choices[0].message.tool_calls[0]
        if not tool_call or tool_call.function.name != "get_content":
            return base_response

        messages.append(
            {
                "role": "assistant",
                "tool_calls": [tool_call.dict()],
            }
        )

        tc_args = json.loads(tool_call.function.arguments)
        messages.append(self._execute_tool_call(**tc_args, tool_call_id=tool_call.id))
        return self._get_messages_response(prompt_request, messages)
