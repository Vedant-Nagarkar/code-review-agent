from langchain_openai import ChatOpenAI
from core.config import settings


def get_llm() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set — required to create an LLM client.")
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=settings.llm_temperature,
    )