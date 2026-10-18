FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN groupadd --system --gid 10001 forgeclaw && useradd --system --uid 10001 --gid forgeclaw --home-dir /home/forgeclaw forgeclaw
COPY pyproject.toml README.md ./
COPY forgeclaw ./forgeclaw
COPY prompts ./prompts
RUN pip install --no-cache-dir .
RUN mkdir -p /app/data /app/logs && chown -R forgeclaw:forgeclaw /app
USER 10001:10001
ENV FORGECLAW_DATABASE_PATH=/app/data/forgeclaw.sqlite3
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)"
CMD ["uvicorn", "forgeclaw.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
