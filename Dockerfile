FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

ENV DEBUG=False
ENV ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

COPY .env ./
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/static /app/uploads /app/staticfiles

RUN python3 manage.py collectstatic --noinput

EXPOSE 8000 8081

CMD ["gunicorn", "-c", "askme_chukhvichev/wsgi_config.py", "askme_chukhvichev.wsgi:application"]