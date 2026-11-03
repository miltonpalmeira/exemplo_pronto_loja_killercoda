#!/bin/bash
# Sobe junto com o Postgres, uma vez, com o disco vazio.
# Conceito, UN3 S1 — memória privada: dois bancos. O estoque não lê o limite.
# A loja não tem usuário aqui. Ela só recebe a mensagem HTTP.

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
CREATE DATABASE estoque;
CREATE DATABASE pagamento;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname estoque <<EOSQL
CREATE TABLE saldo (
    item TEXT PRIMARY KEY,
    quantidade INTEGER NOT NULL
);
INSERT INTO saldo (item, quantidade) VALUES ('camiseta', 4);
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname pagamento <<EOSQL
CREATE TABLE limite (
    id INTEGER PRIMARY KEY,
    valor NUMERIC(10, 2) NOT NULL
);
INSERT INTO limite (id, valor) VALUES (1, 500.00);
EOSQL
