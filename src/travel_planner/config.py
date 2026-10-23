"""STEP 1 - Build the chat model from environment variables."""
import os

from dotenv import load_dotenv

load_dotenv()


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    if provider == "groq":
        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
        from langchain_groq import ChatGroq

        return ChatGroq(model=model, temperature=0.2, max_retries=4)

    # if provider == "ollama":
    #     from langchain_ollama import ChatOllama

    #     return ChatOllama(model=model, temperature=0.2)

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (use 'groq' or 'ollama')")