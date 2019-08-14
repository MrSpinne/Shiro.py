# Shiro.py - Work in progress
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/d668927a72f14c19b23ca9a0ed71fb20)](https://www.codacy.com/app/MrSpinne/Shiro.py?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=MrSpinne/Shiro.py&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/d668927a72f14c19b23ca9a0ed71fb20)](https://www.codacy.com/app/MrSpinne/Shiro.py?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=MrSpinne/Shiro.py&amp;utm_campaign=Badge_Coverage)
[![Build Status](https://travis-ci.org/MrSpinne/Shiro.py.svg?branch=master)](https://travis-ci.org/MrSpinne/Shiro.py)
[![Crowdin](https://badges.crowdin.net/shiro-py/localized.svg)](https://crowdin.com/project/shiro-py)

![Python Version](https://img.shields.io/badge/python-3.7-blue)
![Bot Version](https://img.shields.io/badge/version-1.3-orange)
![Discord Server](https://img.shields.io/discord/600761022089003021)
![License](https://img.shields.io/github/license/MrSpinne/Shiro.py)

Want to guess anime openings with your friends? 
Get Shiro to play song quizzes and enhance your guild with fun related anime features!

## Table of Contents
*   [Setup](#setup)
    *   [Docker](#docker)
    *   [Postgres Database](#postgres-database)
    *   [Lavalink Server](#lavalink-server)
    *   [Shiro](#shiro)
    *   [Watchtower](#watchtower)

*   [Configuration](#configuration)
    *   [Config options](#config-options)
    *   [Environmental Variables](#environmental-variables)

*   [Contribute](#contribute)

*   [Links](#links)

*   [Bot lists](#bot-lists)

## Setup
The following setup is done with **docker on debian**. If you're using another os, it may variate a bit.
If you don't like docker, you can also install everything on your own. But be aware, **you won't get automatic patches** then!

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
docker run --rm --name postgres -e POSTGRES_DATABASE=shiro -e POSTGRES_USER=shiro -e POSTGRES_PASSWORD=shiro -d -p 5432:5432 -v $HOME/docker/volumes/postgres:/var/lib/postgresql/data postgres
```

### Lavalink Server
Also, you have to setup a Lavalink server in order for the bot to play music. 
[More about Lavalink](https://github.com/Frederikam/Lavalink)
```bash
docker pull fredboat/lavalink:master
mkdir -p $HOME/docker/volumes/lavalink
nano $HOME/docker/volumes/lavalink/application.yml # Paste default config from Lavalink and set password
docker docker run --rm --name lavalink -v $HOME/docker/volumes/lavalink/application.yml:/opt/Lavalink/application.yml -d -p 2333:2333 fredboat/lavalink:master
```

### Shiro
After installing and running all requirements, we finally can start Shiro. It will automatically create all tables in 
the database. [Configure](#configuration)
```bash
docker pull mrspinne/shiro.py:master
docker run --rm --name shiro -e DISCORD_TOKEN=shiro -d mrspinne/shiro.py:master
```

### Watchtower
The following will keep you docker container up to date. If you only want to auto update specific container, 
[have a look here](https://containrrr.github.io/watchtower/arguments/).
```bash
docker pull containrrr/watchtower
docker run --rm --name watchtower -d -v /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower
```

## Configuration
The configuration file is located in `data/config.ini`. If you use docker, it's recommended to pass config values via 
[environmental variables](https://docs.docker.com/engine/reference/commandline/run/#options) (or you mount the config). 

### Config options
Please note that sections marked with `optional` in the `config.ini` aren't supposed to be used by you. 
[Create a Discord application](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token)

**config.ini** (the part you have to configure)
```ini
[Discord]
token = 

[Postgres]
host =
port =
database =
user =
password =

[Lavalink]
host =
port =
password =
region =
```

### Environmental Variables
If you want to use envs, here is how to pass them. You can look up them from the config.
Example envs: `DISCORD_TOKEN`, `POSTGRES_HOST`, `POSTGRES_PORT`, `LAVALINK_PASSWORD`

## Contribute
I'd like to hear your thoughts about the whole project. It's far from perfect so feel free to contribute.

## Links
*   [Website](https://shiro.pro)
*   [Support Server](https://discord.gg/5z4z8kh)
*   [Discord Bots](https://discordbots.org/bot/593116701281746955)
*   [Invite Bot](https://discordapp.com/oauth2/authorize?client_id=593116701281746955&permissions=3238976&scope=bot)

## Bot lists
Below are all bot lists, Shiro is currently on. (Only lists with widget shown)

[<img src="https://discordbots.org/api/widget/593116701281746955.svg" height="150">](https://discordbots.org/bot/593116701281746955)
[<img src="https://discordbotlist.com/bots/593116701281746955/widget" height="150">](https://discordbotlist.com/bots/593116701281746955)
[<img src="https://divinediscordbots.com/api/widget/593116701281746955.svg" height="150">](https://divinediscordbots.com/bot/593116701281746955)
[<img src="https://discord.boats/api/widget/593116701281746955" height="150">](https://discord.boats/bot/593116701281746955)
[<img src="https://bots.ondiscord.xyz/bots/593116701281746955/embed?theme=dark&showGuilds=true" height="150">](https://bots.ondiscord.xyz/bots/593116701281746955)