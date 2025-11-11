FROM ubuntu:20.04

RUN \
    apt update \
    && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt install -y software-properties-common git pipenv ffmpeg gcc g++ make libffi-dev python3-dev curl


# RUN add-apt-repository ppa:deadsnakes/ppa && \
#     apt update && \
#     apt install -y python3.9 python3.9-dev python3.9-distutils


# RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.9

WORKDIR free-loaders

COPY Pipfile Pipfile.lock ./
RUN apt-get update && apt-get install -y gcc libffi-dev python3-dev
RUN pipenv install --python 3.8
COPY classes classes/
COPY executor executor/
COPY flomqtt flomqtt/

EXPOSE 8088/tcp
ENV PYTHONPATH=. \
    CONTROLLER_IP=10.1.1.3 \
    EXEC_ID=0 \
    ENERGY_VAL=2.05 \
    EXEC_NAME=rpi4 \
    NET_IF=container \
    NET_CAP=1000 \
    PERF_PATH=/bin/perf
WORKDIR /home/vboxuser/free-loaders/executor
CMD ["pipenv", "run", "python", "flexecutor", "-l", "d", "10.1.1.3", "0", "2.05"]
