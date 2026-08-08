import httpx
from core.config import settings

API_URL = getattr(settings, "api_url", "http://localhost:8080")
TIMEOUT_SECONDS = 180  # LLM calls + retries can take a while


def run_review(code: str, language: str = "python", filename: str = "unnamed.py") -> dict:
    try:
        response = httpx.post(
            f"{API_URL}/review",
            json={"code": code, "language": language, "filename": filename},
            timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        return {"error": "Review service did not respond in time."}
    except httpx.ConnectError:
        return {"error": "Could not connect to the review API — it may be down."}
    except httpx.HTTPStatusError as e:
        return {"error": f"API returned an error: {e.response.status_code} — {e.response.text}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}