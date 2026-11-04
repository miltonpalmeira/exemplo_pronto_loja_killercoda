#!/bin/bash
# Conceito, UN4 S2 — esta Ubuntu já traz o Docker. O plugin do Compose nem sempre vem junto.
# Sem ele, "docker compose up --build" cai no docker e responde: unknown flag: --build.

if ! command -v curl >/dev/null 2>&1; then
  apt-get update
  apt-get install -y curl
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Instalando o Docker Compose."
  mkdir -p "$HOME/.docker/cli-plugins"
  curl -fsSL "https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64" \
    -o "$HOME/.docker/cli-plugins/docker-compose"
  chmod +x "$HOME/.docker/cli-plugins/docker-compose"
  docker compose version
fi

echo "Arquivos prontos em ~/loja"
find ~/loja -type f | sort
