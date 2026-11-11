FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY scripts scripts

EXPOSE 8000

CMD ["sh", "-c", "python scripts/seed_data.py && python scripts/seed_project_interest.py && exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 'app:create_app()'"]
