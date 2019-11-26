FROM python:3.7-slim-buster

RUN apt-get update -y\
  && apt-get install \
    postgresql \
    postgresql-client \
    -y

RUN mkdir /usr/src/app
WORKDIR /usr/src/app
COPY ./requirements.txt .
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED 1

COPY . .
