FROM debian:buster

RUN apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get install -y --no-install-recommends python3.7 python3-pip libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY . .
RUN python3 -m pip3 install -U pip setuptools
RUN pip3 install -r requirements.txt

ENV POSTGRES_HOST localhost
ENV POSTGRES_PORT 5432
ENV POSTGRES_DATABASE shiro
ENV POSTGRES_USER shiro
ENV POSTGRES_PASSWORD shiro
ENV LAVALINK_HOST localhost
ENV LAVALINK_PORT 2333
ENV LAVALINK_PASSWORD shiro
ENV LAVALINK_REGION eu

ENTRYPOINT ["python3", "shiro.py"]