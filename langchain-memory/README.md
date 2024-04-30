## How to Run

- It is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) to run this example.
- Python 3.9.6+ is required.
- pip v24.0.0+ is required.

```bash
# OpenAI API is used in this example.
# Thus, you need to have an API key and set it as an environment variable.
export OPENAI_API_KEY={API_KEY}

# Install dependencies.
pip install -r requirements.txt

# Run the server.
uvicorn main:app --reload
```
