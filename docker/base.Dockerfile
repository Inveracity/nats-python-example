FROM python:3.12-bookworm

ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV PYTHONUNBUFFERED=0

RUN apt update -qq && apt install -y python3-pip
RUN pip install poetry

RUN mkdir -p /code
COPY . /code
WORKDIR /code

RUN poetry install
