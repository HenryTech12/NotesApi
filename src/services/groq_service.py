# src/services/groq_service.py
import os
import asyncio
import time
import hashlib
import random
from typing import Optional, Tuple, List
import httpx
import json

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Simple in-memory cache: key -> (value, ts)
_cache = {}
_CACHE_TTL = 3600  # 1 hour

async def _request_with_retries(messages: List[dict], model: str = DEFAULT_MODEL, timeout: float = 30.0, max_retries: int = 3) -> dict:
    if not GROQ_API_KEY or "your_key_here" in GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not set or invalid"}

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
    }

    backoff_base = 1.0

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, max_retries + 1):
            try:
                resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
                
                if resp.status_code == 200:
                    return resp.json()
                
                # Rate limit (429) or Server error (5xx) - retryable
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    if attempt == max_retries:
                        return {"error": f"Groq API error after {max_retries} retries: {resp.status_code}"}
                else:
                    # Non-retryable error
                    return {"error": f"Groq API non-retryable error: {resp.status_code} {resp.text}"}

            except (httpx.RequestError, httpx.TimeoutException) as exc:
                if attempt == max_retries:
                    return {"error": f"Groq API connection error: {str(exc)}"}
            
            # Exponential backoff with jitter
            sleep_time = backoff_base * (2 ** (attempt - 1)) + random.uniform(0, 1)
            await asyncio.sleep(sleep_time)
    
    return {"error": "Unknown failure"}

def _cache_get(key: str) -> Optional[str]:
    val = _cache.get(key)
    if not val:
        return None
    value, ts = val
    if time.time() - ts > _CACHE_TTL:
        del _cache[key]
        return None
    return value

def _cache_set(key: str, value: str) -> None:
    _cache[key] = (value, time.time())

def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

async def summarize(text: str, model: Optional[str] = None) -> Tuple[Optional[str], dict]:
    if not text:
        return None, {"error": "No text provided"}
    
    content_hash = _content_hash(text)
    cache_key = f"summary:{content_hash}"
    cached = _cache_get(cache_key)
    if cached:
        return cached, {"cached": True}

    messages = [
        {"role": "system", "content": "Summarize the following note content concisely (max 2 sentences)."},
        {"role": "user", "content": text}
    ]

    result = await _request_with_retries(messages, model=model or DEFAULT_MODEL)
    
    if "error" in result:
        return None, result

    try:
        summary = result["choices"][0]["message"]["content"].strip()
        _cache_set(cache_key, summary)
        return summary, {"cached": False}
    except (KeyError, IndexError) as e:
        return None, {"error": f"Invalid response format: {str(e)}"}

async def suggest_tags(text: str, model: Optional[str] = None) -> Tuple[List[str], dict]:
    if not text:
        return [], {"error": "No text provided"}

    content_hash = _content_hash(text)
    cache_key = f"tags:{content_hash}"
    cached = _cache_get(cache_key)
    if cached:
        return json.loads(cached), {"cached": True}

    messages = [
        {"role": "system", "content": "Suggest 3-5 relevant tags for this note. Return only a comma-separated list of tags, no other text."},
        {"role": "user", "content": text}
    ]

    result = await _request_with_retries(messages, model=model or DEFAULT_MODEL)
    if "error" in result:
        return [], result

    try:
        tags_raw = result["choices"][0]["message"]["content"].strip()
        # Handle cases where LLM might return "Tags: a, b, c"
        if ":" in tags_raw:
            tags_raw = tags_raw.split(":", 1)[1]
        tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
        _cache_set(cache_key, json.dumps(tags))
        return tags, {"cached": False}
    except (KeyError, IndexError) as e:
        return [], {"error": f"Invalid response format: {str(e)}"}
