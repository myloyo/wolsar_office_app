FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./
COPY app ./app
RUN pip install --no-cache-dir -r requirements.lock
COPY alembic.ini ./
COPY migrations ./migrations
RUN useradd --create-home office && mkdir -p /app/uploads && chown -R office:office /app
USER office
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"]
