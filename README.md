# EllmO
#### E[nhanced]llm[O]perator

EllmO is a drop-in replacement for OpenAI's API chat completion endpoint.

## Installation

1. Clone the repository

2. Install packages with Poetry:
    ```sh
    poetry install
    ```

    Alternatively, you can create and activate a virtual environment, then install the dependencies:
    ```sh
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. Create a [.env](http://_vscodecontentref_/1) file in the root directory and add your OpenAI API key:
    ```env
    OPENAI_API_KEY=your_openai_api_key
    ```

## Usage

1. Run the FastAPI server:
    ```sh
    (poetry run) python main.py
    ```