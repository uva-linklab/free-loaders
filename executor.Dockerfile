FROM ubuntu:20.04

RUN apt update && apt install -y git pipenv

WORKDIR free-loaders

COPY Pipfile Pipfile.lock ./
RUN pipenv install
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
CMD ["pipenv", "run", "python", "executor/flexecutor", "-l", "d", "10.1.1.3", "0", "2.05"]
