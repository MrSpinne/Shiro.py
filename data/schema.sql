create table if not exists guilds
  (
    id                  bigint                       not null,
    prefix              text      default 's.'::text not null,
    invocation_deletion boolean   default false      not null,
    restricted_channel  bigint,
    language            text      default 'en-US'::text not null,
    constraint guilds_pk
    primary key (id)
  );

  alter table guilds
  owner to specify_user;

  create unique index guilds_id_uindex
  on guilds (id);

create table if not exists songs
  (
    id        bigint                  not null,
    title     text                    not null,
    reference text                    not null,
    url       text                    not null,
    category  text                    not null,
    constraint songs_pk
    primary key (id)
  );

  alter table songs
  owner to specify_user;

  create unique index songs_id_uindex
  on songs (id);

create table if not exists users
  (
    id        bigint not null,
    last_vote timestamp,
    constraint users_pk
    primary key (id)
  );

  alter table users
  owner to specify_user;

  create unique index users_id_uindex
  on users (id);
