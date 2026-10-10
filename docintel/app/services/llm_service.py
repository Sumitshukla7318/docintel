"""
Wrapper around Google Gemini (free tier). Isolated here so swapping models
or providers later only touches this one file.
"""
from functools import lru_cache

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


@lru_cache
def _get_model() -> genai.GenerativeModel:
    return genai.GenerativeModel(settings.GEMINI_MODEL)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_answer(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    """
    Retries with exponential backoff to smooth over transient free-tier rate
    limits (429s) — a real production concern with free API tiers.
    """
    model = _get_model()
    response = model.generate_content(
        [
            {"role": "user", "parts": [system_prompt + "\n\n" + user_prompt]},
        ],
        generation_config=genai.types.GenerationConfig(temperature=temperature),
    )
    return response.text.strip()


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
def condense_query(history: str, question: str) -> str:
    from app.utils.prompt import QUERY_CONDENSE_PROMPT

    model = _get_model()
    prompt = QUERY_CONDENSE_PROMPT.format(history=history, question=question)
    response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.0))
    return response.text.strip()