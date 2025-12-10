FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN mkdir -p transfer

EXPOSE 8089

CMD ["gunicorn", "--bind", "0.0.0.0:8089", "--workers", "4", "app:app"]
