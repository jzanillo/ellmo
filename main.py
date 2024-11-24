import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from ellmo.routes.chat.core import PromptExecutor
from ellmo.internal.models import ChatCompletionRequest, ChatCompletionResponse

load_dotenv()

open_api_key = os.getenv("OPENAI_API_KEY")
if open_api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

prompt_executor = PromptExecutor(open_api_key=open_api_key, max_results=3)
app = FastAPI(title="EllmO Chat API")


@app.post("/chat", response_model=ChatCompletionResponse)
def post_chat_completion(request: ChatCompletionRequest):
    try:
        return prompt_executor.execute(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
