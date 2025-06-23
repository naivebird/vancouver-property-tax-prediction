FROM python:3.12

WORKDIR /app

COPY . /app

RUN pip install pipenv

RUN pipenv install

EXPOSE 8000

CMD ["uvicorn", "serve_model:app", "--host", "0.0.0.0", "--port", "8000"]
