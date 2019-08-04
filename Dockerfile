FROM debian:stretch

RUN apt-get update && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install python3.7 -y
RUN apt install git -y
RUN apt install python3-pip -y
RUN apt install libpq-dev -y
RUN git clone https://github.com/MrSpinne/Shiro.py.git
RUN cp -a Shiro.py/. .
RUN rm -rf Shiro.py/
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