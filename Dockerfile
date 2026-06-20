FROM python:3.14-slim

# ── Python env settings ───────────────────────
# PYTHONDONTWRITEBYTECODE — stops Python writing .pyc files inside the container
# PYTHONUNBUFFERED — forces stdout/stderr to flush immediately so 'docker logs' shows output live

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


# All files land under /app inside the container
WORKDIR /app

# ── Install dependencies ──────────────────────
# if requirements.txt hasn't changed, this pip install is skipped
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy the Django project ───────────────────
# Copies KORNERCLOUD/core/ -> /app/core/ inside container
# .env is NOT copied — it's mounted at runtime via docker-compose so secrets never bake into the image
COPY core/ ./core/

# This is where manage.py and gunicorn.conf.py live
WORKDIR /app/core

# ── Startup command ───────────────────────────
# Runs three things in sequence every time the container starts:
# 1. migrate        — applies any pending DB migrations
#                     (creates YouKnow user on first run
#                      via the data migration)

# 2. collectstatic  — gathers all static files into
#                     staticfiles/ so nginx can serve them

# 3. gunicorn       — starts the app server with our config
CMD ["sh", "-c", \
     "python manage.py migrate --noinput && \
      python manage.py collectstatic --noinput && \
      gunicorn --config gunicorn.conf.py core.wsgi:application"]
