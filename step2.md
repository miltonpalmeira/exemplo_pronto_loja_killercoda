# Criar o pagamento

O mesmo formato, outro database. Conceito, UN3 S1 — a tabela `limite` não está no estoque. Ainda não há paralelo: cada serviço, sozinho, é um cliente-servidor.

```bash
cat > ~/loja/pagamento/requirements.txt << 'EOF'
fastapi>=0.115
uvicorn>=0.32
psycopg[binary]>=3.2
EOF
```

```bash
cat > ~/loja/pagamento/Dockerfile << 'EOF'
# Conceito, UN4 S2 — contêiner. O pagamento não enxerga o saldo do estoque.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
HEALTHCHECK --interval=2s --timeout=1s --start-period=5s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

```bash
cat > ~/loja/pagamento/app.py << 'EOF'
# Pagamento — um processo e o banco dele: o limite de R$ 500.
# Conceito, UN3 S1 — a tabela limite está no banco pagamento.
# Conceito, UN3 S4 — POST /autorizar é o contrato. A loja manda só o valor.

import os
import time

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Conceito, UN3 S2 — nomeação. Mesmo servidor, outro database.
DATABASE_URL = os.environ["PAGAMENTO_DATABASE_URL"]

# Conceito, UN4 S1 — o mesmo 0,4 s do estoque.
# Em sequência a loja paga a soma. Em paralelo, um dos dois.
TEMPO_ATENDIMENTO = 0.4


class Autorizacao(BaseModel):
    valor: float


def ler_limite():
    with psycopg.connect(DATABASE_URL) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT valor FROM limite WHERE id = 1")
            linha = cursor.fetchone()
    return float(linha[0])


@app.get("/health")
def health():
    with psycopg.connect(DATABASE_URL) as conexao:
        conexao.execute("SELECT 1")
    return {"status": "up", "servico": "pagamento"}


@app.post("/autorizar")
def autorizar(pedido: Autorizacao):
    time.sleep(TEMPO_ATENDIMENTO)
    limite = ler_limite()
    if pedido.valor <= limite:
        status = "APROVADO"
        mensagem = "Pagamento autorizou: o valor cabe no limite de R$ 500,00."
    else:
        status = "RECUSADO"
        mensagem = "Pagamento recusou: o valor passa do limite de R$ 500,00."
    print(f"pagamento valor={pedido.valor:.2f} limite={limite:.2f} {status}", flush=True)
    return {"status": status, "mensagem": mensagem}
EOF
```
