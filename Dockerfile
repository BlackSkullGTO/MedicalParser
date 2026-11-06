FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# tzdata нужен для корректной работы таймзон (ZoneInfo / TZ / PostgreSQL).
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \
    playwright install-deps chromium

# Непривилегированный пользователь: chromium требует его для работы песочницы.
RUN useradd --create-home --uid 1000 app && \
    chown -R app:app /ms-playwright

COPY --chown=app:app . .

USER app

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "app.cli", "worker", "--loglevel=info", "--concurrency=1"]
