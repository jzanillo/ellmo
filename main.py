import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from ellmo.routes.chat.core import PromptExecutor
from ellmo.internal.models import ChatCompletionRequest, ChatCompletionResponse

load_dotenv()

OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
if OPEN_API_KEY is None:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", 3))

prompt_executor = PromptExecutor(
    open_api_key=OPEN_API_KEY, max_results=MAX_SEARCH_RESULTS
)
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
