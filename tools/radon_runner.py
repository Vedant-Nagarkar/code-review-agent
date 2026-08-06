import subprocess
import tempfile
import os


def run_radon(code: str, language: str) -> str:
    # Radon only works on Python code
    if language.lower() != "python":
        return "Radon analysis skipped — only supported for Python code."

    # Write code to a temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        # cc = cyclomatic complexity, mi = maintainability index
        cc_result = subprocess.run(
            ["radon", "cc", tmp_path, "-s", "-a"],
            capture_output=True,
            text=True,
            timeout=30
        )

        mi_result = subprocess.run(
            ["radon", "mi", tmp_path, "-s"],
            capture_output=True,
            text=True,
            timeout=30
        )

        cc_output = cc_result.stdout.strip()
        mi_output = mi_result.stdout.strip()

        if not cc_output and not mi_output:
            return "Radon found no complexity issues."

        output_parts = []
        if cc_output:
            output_parts.append(f"Cyclomatic Complexity:\n{cc_output}")
        if mi_output:
            output_parts.append(f"Maintainability Index:\n{mi_output}")

        return "\n\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return "Radon analysis timed out after 30 seconds."

    except FileNotFoundError:
        return "Radon not found — ensure it is installed in the environment."

    except Exception as e:
        return f"Radon analysis failed: {str(e)}"

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)