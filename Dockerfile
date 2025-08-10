FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-root

COPY . .

RUN curl -sSLo /usr/local/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
 && chmod +x /usr/local/bin/wait-for-it

EXPOSE 8000

CMD ["wait-for-it","db:5432","--","sh","-c","python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn djangoweatherreminder.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 60"]
