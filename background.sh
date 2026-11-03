#!/bin/bash
# Enquanto a turma lê e escreve o código, as imagens começam a baixar.
# O paralelo não está neste script.

for _ in $(seq 1 30); do
  if [ -f "$HOME/loja/docker-compose.yml" ]; then
    break
  fi
  sleep 1
done

if [ -f "$HOME/loja/docker-compose.yml" ]; then
  cd "$HOME/loja"
  docker compose pull banco
  docker compose build
fi
