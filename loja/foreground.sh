#!/bin/bash
# Conceito, UN4 S2 — esta Ubuntu já traz o Docker. Os arquivos da loja chegam pela pasta assets.

if ! command -v curl >/dev/null 2>&1; then
  apt-get update
  apt-get install -y curl
fi

echo "Arquivos prontos em ~/loja"
find ~/loja -type f | sort
