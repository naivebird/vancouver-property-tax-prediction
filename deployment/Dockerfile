FROM python:3.12-slim

WORKDIR /app

COPY Pipfile Pipfile.lock /app/

RUN pip install --no-cache-dir pipenv \
    && pipenv install --deploy --ignore-pipfile \
    && apt-get purge -y --auto-remove \
    && rm -rf /root/.cache

COPY . /app

EXPOSE 8000

CMD ["pipenv", "run", "uvicorn", "serve_model:app", "--host", "0.0.0.0", "--port", "8000"]