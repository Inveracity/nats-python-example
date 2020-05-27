FROM python:3.8-slim-buster

RUN pip install pipenv

RUN mkdir -p /code
COPY . /code
WORKDIR /code

RUN pipenv install
