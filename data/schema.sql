create table if not exists guilds
  (
    id                  bigint                       not null,
    prefix              text      default 's.'::text not null,
    invocation_deletion boolean   default false      not null,
    restrict_channel    bigint,
    language            text      default 'en'::text not null,
    updated             timestamp default now()      not null,
    constraint guilds_pk
    primary key (id)
  );

  alter table guilds
  owner to shiro;

  create unique index guilds_id_uindex
  on guilds (id);

create table if not exists songs
  (
    id        bigint                  not null,
    title     text                    not null,
    reference text                    not null,
    url       text                    not null,
    category  text                    not null,
    updated   timestamp default now() not null,
    constraint songs_pk
    primary key (id)
  );

  alter table songs
  owner to shiro;

  create unique index songs_id_uindex
  on songs (id);

create table if not exists users
  (
    id        bigint not null,
    last_vote timestamp,
    updates   timestamp default now() not null,
    constraint users_pk
    primary key (id)
  );

  alter table users
  owner to shiro;

  create unique index users_id_uindex
  on users (id);
