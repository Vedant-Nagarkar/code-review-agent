FROM python:3.11-slim

WORKDIR /app

# Install only what the sandbox needs — not the full project requirements.
# Keeping this minimal reduces attack surface and image size.
RUN pip install --no-cache-dir fastapi uvicorn pydantic

COPY main.py .
COPY runner.py .

# Run as a non-root user — if sandboxed code somehow escapes the subprocess
# containment, it still can't do root-level damage inside the container.
RUN useradd -m sandboxuser
USER sandboxuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]