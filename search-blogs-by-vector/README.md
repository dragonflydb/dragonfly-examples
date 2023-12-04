# Example: Search Blogs by Dragonfly Vector Search

In this example, we will build a search engine for Dragonfly blogs using Dragonfly Vector Search with the OpenAI API.

## Local Setup

- The following steps assume that you are working in the root directory of this example (dragonfly-examples/search-blogs-by-vector).
- Start with a clean Python environment:

```shell
python3 -m venv venv
```

- After the virtual environment is created, activate it:

```shell
# Windows
venv\Scripts\activate
```

```shell
# Linux / macOS
source venv/bin/activate
```

- Install Jupyter Notebook and other dependencies:

```shell
(venv)$> pip install notebook==7.0.6
(venv)$> pip install openai==1.3.7
(venv)$> pip install pandas==2.1.3
(venv)$> pip install numpy==1.26.2
(venv)$> pip install redis==5.0.1
```

## Run Dragonfly & Jupyter Notebook

- Run a Dragonfly instance using Docker (v1.13 or above) locally:

```bash
docker run -p 6379:6379 --ulimit memlock=-1 ghcr.io/dragonflydb/dragonfly:v1.13.0-ubuntu
```

- Run Jupyter Notebook server locally:

```shell
(venv)$> jupyter notebook
```

- Run cells in `search-blogs-by-vector.ipynb` from the Jupyter Notebook Web UI at `http://localhost:8888/`
