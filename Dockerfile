FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False
ENV ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,web,nginx,centrifugo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/static /app/uploads /app/staticfiles

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "-c", "askme_chukhvichev/wsgi_config.py", "askme_chukhvichev.wsgi:application"]