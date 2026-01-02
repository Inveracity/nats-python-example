FROM python:3.12-bookworm

ENV PYTHONUNBUFFERED=0

RUN apt update -qq && apt install -y python3-pip
RUN pip install uv

RUN mkdir -p /code
COPY . /code
WORKDIR /code

RUN uv sync
