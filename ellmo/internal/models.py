from typing import List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str
    tool_calls: Optional[str] = None


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float | None = None
    max_completion_tokens: int | None = None


class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: str
    choices: List[Choice]
    usage: CompletionUsage


class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
