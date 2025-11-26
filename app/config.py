import os

MODEL_NAME = os.getenv("LLM_MODEL", "mistral")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")