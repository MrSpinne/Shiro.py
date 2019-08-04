# Shiro.py - WIP
![Build Status](https://api.travis-ci.org/MrSpinne/Shiro.py.svg?branch=master)
![Codacy Badge](https://api.codacy.com/project/badge/Grade/d668927a72f14c19b23ca9a0ed71fb20)

![Python Version](https://img.shields.io/badge/python-3.7-blue)
![Bot Version](https://img.shields.io/badge/version-1.3-orange)
![Discord Server](https://img.shields.io/discord/600761022089003021)

[![Discord Bots](https://discordbots.org/api/widget/593116701281746955.svg)](https://discordbots.org/bot/593116701281746955)

Want to guess anime openings with your friends? Get Shiro to play song quizzes and enhance your guild with fun related anime features!

## Table of Contents
*   [Setup](#setup)
    *   [Docker](#docker)
    *   [Postgres Database](#postgres-database)
    *   [Lavalink Server](#lavalink-server)
    *   [Shiro](#shiro)
*   [Links](#links)

## Setup
The following setup is done with **docker on debian**. If you're using another os, it may variate a bit.

### Docker
First of all you need to install docker. 
[Check this tutorial](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-debian-9)
```bash
sudo apt-get update
sudo apt install apt-transport-https ca-certificates curl gnupg2 software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
sudo apt update
sudo apt install docker-ce
```

### Postgres Database
Then you have to download and run the postgres docker image and mount it to a dir.
```bash
docker pull postgres
mkdir -p $HOME/docker/volumes/postgres
docker run --rm --name postgres -e POSTGRES_DATABASE=shiro -e POSTGRES_USER=shiro -e POSTGRES_PASSWORD=shiro -d -v $HOME/docker/volumes/postgres:/var/lib/postgresql/data postgres
```

### Lavalink Server
Also, you have to setup a Lavalink server in order for the bot to play music. [More about Lavalink](https://github.com/Frederikam/Lavalink)
```bash
docker pull fredboat/lavalink
docker run --rm -name lavalink -e LAVALINK_SERVER_PASSWORD=shiro -d fredboat/lavalink
```

### Shiro
After installing and running all requirements, we finally can start Shiro. [Configure]()
```bash
docker pull mrspinne/shiro.py
docker run --rm name shiro -e DISCORD_TOKEN=shiro -d mrspinne/shiro.py
```

## Links
*   [Support Server](https://discord.gg/5z4z8kh)
*   [Discord Bots](https://discordbots.org/bot/593116701281746955)
*   [Invite Bot](https://discordapp.com/oauth2/authorize?client_id=593116701281746955&permissions=3238976&scope=bot)
