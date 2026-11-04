# Criar o banco e o estoque

A pasta está vazia. Este passo grava o banco e o serviço de estoque. Ainda não sobe nada.

Conceito, UN3 S1 — dois databases. A loja não entra neste script.

```bash
cat > ~/loja/postgres/init.sh << 'EOF'
#!/bin/bash
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
EOF
chmod +x ~/loja/postgres/init.sh
```

Conceito, UN3 S4 — FastAPI. A rota é o contrato. A função lê com `SELECT` e não dá `UPDATE`.

```bash
cat > ~/loja/estoque/requirements.txt << 'EOF'
fastapi>=0.115
uvicorn>=0.32
psycopg[binary]>=3.2
EOF
```

```bash
cat > ~/loja/estoque/Dockerfile << 'EOF'
# Conceito, UN4 S2 — contêiner. Empacota só este serviço.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
# 0.0.0.0: outro contêiner precisa alcançar esta porta. Em 127.0.0.1, não alcança.
HEALTHCHECK --interval=2s --timeout=1s --start-period=5s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

```bash
cat > ~/loja/estoque/app.py << 'EOF'
# Estoque — um processo e o banco dele: quantas camisetas existem.
# Conceito, UN3 S1 — a tabela saldo está no banco estoque. A loja não conecta.
# Conceito, UN3 S4 — POST /consultar é o contrato.

import os
import time

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Conceito, UN3 S2 — nomeação. O nome na rede é "banco".
DATABASE_URL = os.environ["ESTOQUE_DATABASE_URL"]

# Conceito, UN4 S1 — latência. O Postgres local é rápido demais.
# 0,4 s segura o lugar da ida a um banco remoto.
TEMPO_ATENDIMENTO = 0.4


class Consulta(BaseModel):
    item: str
    qtd: int


def ler_saldo(item):
    # SELECT, não UPDATE. A consulta não baixa a prateleira.
    with psycopg.connect(DATABASE_URL) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                "SELECT quantidade FROM saldo WHERE item = %s",
                (item,),
            )
            linha = cursor.fetchone()
    if linha is None:
        return 0
    return int(linha[0])


@app.get("/health")
def health():
    with psycopg.connect(DATABASE_URL) as conexao:
        conexao.execute("SELECT 1")
    return {"status": "up", "servico": "estoque"}


@app.post("/consultar")
def consultar(pedido: Consulta):
    time.sleep(TEMPO_ATENDIMENTO)
    disponivel = ler_saldo(pedido.item)
    if disponivel >= pedido.qtd:
        status = "TEM"
        mensagem = (
            f"Consulta: há {disponivel} {pedido.item}. "
            f"Pedir {pedido.qtd} cabe. O saldo continua {disponivel}."
        )
    else:
        status = "SEM_ESTOQUE"
        mensagem = (
            f"Consulta: há {disponivel} {pedido.item}. "
            f"Pedir {pedido.qtd} não cabe. O saldo continua {disponivel}."
        )
    print(
        f"estoque consulta {pedido.item} qtd={pedido.qtd} saldo={disponivel} (não baixou) {status}",
        flush=True,
    )
    return {"status": status, "mensagem": mensagem, "saldo": disponivel}
EOF
```

Confira que os arquivos nasceram agora:

```bash
find ~/loja -type f | sort
```
