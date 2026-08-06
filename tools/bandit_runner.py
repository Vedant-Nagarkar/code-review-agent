import subprocess
import tempfile
import os


def run_bandit(code: str, language: str) -> str:
    # Bandit only works on Python code
    if language.lower() != "python":
        return "Bandit analysis skipped — only supported for Python code."

    # Write code to a temp file — bandit needs a file path, not stdin
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
            ["bandit", "-r", tmp_path, "-f", "text", "--quiet"],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout.strip()

        # Bandit returns empty stdout if no issues found
        if not output:
            return "Bandit found no security issues."

        return output

    except subprocess.TimeoutExpired:
        return "Bandit analysis timed out after 30 seconds."

    except FileNotFoundError:
        return "Bandit not found — ensure it is installed in the environment."

    except Exception as e:
        return f"Bandit analysis failed: {str(e)}"

    finally:
        # Always clean up the temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)