#!/bin/bash
# A sessão começa sem o código da loja. Quem cria os arquivos é a turma, nos passos.
# Conceito, UN4 S2 — esta Ubuntu já traz o Docker. Não há conta de nuvem.

if ! command -v curl >/dev/null 2>&1; then
  apt-get update
  apt-get install -y curl
fi

mkdir -p ~/loja/estoque ~/loja/pagamento ~/loja/loja ~/loja/postgres
echo "Pasta vazia, pronta para os arquivos: ~/loja"
ls -la ~/loja ~/loja/estoque ~/loja/pagamento ~/loja/loja ~/loja/postgres
