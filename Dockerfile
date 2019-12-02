FROM python:3.7-slim-buster

RUN apt-get update && apt-get install -y \
  postgresql \
  postgresql-client

WORKDIR /usr/src/app
COPY ./requirements.txt .

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED 1

CMD ["bash"]
