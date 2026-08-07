import subprocess
import tempfile
import os
import resource
import signal


MAX_EXECUTION_TIME = 10  # seconds
MAX_MEMORY_MB = 100


def _limit_resources():
    """Called in the child process before exec — caps memory usage."""
    max_memory_bytes = MAX_MEMORY_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))


def run_code(code: str, language: str = "python") -> dict:
    if language.lower() != "python":
        return {
            "success": False,
            "stdout": "",
            "stderr": "Only Python execution is supported.",
            "timed_out": False
        }

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True,
            text=True,
            timeout=MAX_EXECUTION_TIME,
            preexec_fn=_limit_resources,  # applies memory cap in child process
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[:5000],  # cap output size
            "stderr": result.stderr[:2000],
            "timed_out": False
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {MAX_EXECUTION_TIME} seconds — possible infinite loop.",
            "timed_out": True
        }

    except MemoryError:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution exceeded memory limit of {MAX_MEMORY_MB}MB.",
            "timed_out": False
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution failed: {str(e)}",
            "timed_out": False
        }

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)