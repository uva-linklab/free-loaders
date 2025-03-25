# syntax=docker/dockerfile:1

FROM ubuntu:20.04

RUN apt update && apt install -y git pipenv

WORKDIR free-loaders

COPY Pipfile Pipfile.lock docker/executers.json ./
COPY classes classes/
COPY controller controller/
COPY flomqtt flomqtt/

RUN pipenv install

EXPOSE 8001/tcp
ENV PYTHONPATH=.
CMD ["pipenv", "run", "python", "controller/controller.py", "-s", "random", "--mqtt-broker-ip", "10.1.1.3"]
