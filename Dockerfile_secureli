# A basic dockerfile for mimicking/testing ci commands
# docker build -t secureli . or poe docker-build

FROM python:3.9
WORKDIR /app
COPY . /app
RUN pip install poetry
RUN poetry install
RUN poetry run poe precommit
RUN poetry run poe coverage
RUN poetry run secureli yeti
