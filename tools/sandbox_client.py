import httpx
from core.config import settings

SANDBOX_URL = settings.sandbox_url


TIMEOUT_SECONDS = 15  # slightly longer than sandbox's internal 10s execution timeout


def execute_in_sandbox(code: str, language: str = "python") -> dict:
    """
    Calls the sandbox microservice to safely execute code.
    Returns a dict with success, stdout, stderr, timed_out.
    Never raises — always returns a usable dict, even on network failure.
    """
    try:
        response = httpx.post(
            f"{SANDBOX_URL}/run",
            json={"code": code, "language": language},
            timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return response.json()

    except httpx.TimeoutException:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Sandbox did not respond in time — service may be overloaded.",
            "timed_out": True
        }

    except httpx.ConnectError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Could not connect to sandbox service — it may be down.",
            "timed_out": False
        }

    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Sandbox returned an error: {e.response.status_code} — {e.response.text}",
            "timed_out": False
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Unexpected error calling sandbox: {str(e)}",
            "timed_out": False
        }

