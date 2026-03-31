FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN mkdir -p transfer

EXPOSE 8089

CMD sh -c "gunicorn --bind 0.0.0.0:8089 --workers ${WORKERS:-4} --timeout ${TIMEOUT:-180} --graceful-timeout ${GRACEFUL_TIMEOUT:-180} app:app"
