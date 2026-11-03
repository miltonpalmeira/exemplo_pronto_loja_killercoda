# Criar a loja, o Compose e a medida

A loja não tem senha de banco. Conceito, UN3 S2 — ela chama o nome `estoque` e o nome `pagamento`.

A função `em_sequencia` espera uma resposta e só então pede a outra. A função `em_paralelo` é o `asyncio.gather`: as duas mensagens saem juntas. Conceito, UN3 S4 — paralelismo de tarefas. Conceito, UN4 S1 — a espera cai de cerca de 0,8 s para cerca de 0,4 s.

```bash
cat > ~/loja/loja/requirements.txt << 'EOF'
fastapi>=0.115
uvicorn>=0.32
httpx>=0.27
EOF
```

```bash
cat > ~/loja/loja/Dockerfile << 'EOF'
# Conceito, UN4 S2 — contêiner da loja. Só o cliente.
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
cat > ~/loja/loja/app.py << 'EOF'
# Loja — cliente dos dois serviços. Não abre banco e não sobe os outros processos.
# Conceito, UN3 S4 — paralelismo de tarefas: as duas mensagens saem juntas.

import asyncio
import os
import time

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Conceito, UN3 S2 — nomeação. O DNS do Docker resolve o nome.
URL_ESTOQUE = os.environ.get("ESTOQUE_URL", "http://estoque:8000")
URL_PAGAMENTO = os.environ.get("PAGAMENTO_URL", "http://pagamento:8000")

# Conceito, UN3 S1 — falha parcial. Passou de 2 s, silêncio não é um sim.
TIMEOUT_SEGUNDOS = 2.0


class Pedido(BaseModel):
    qtd: int
    valor: float
    modo: str = "paralelo"


def decidir(estoque, pagamento):
    # CONFIRMADA só com TEM e APROVADO.
    if estoque.get("status") == "TEM" and pagamento.get("status") == "APROVADO":
        return "CONFIRMADA"
    return "NAO_CONFIRMADA"


async def pedir(cliente, url, corpo):
    # Conceito, UN1 S4 — passagem de mensagem.
    try:
        resposta = await cliente.post(url, json=corpo, timeout=TIMEOUT_SEGUNDOS)
        return resposta.json()
    except httpx.HTTPError as erro:
        return {"status": "FALHA", "mensagem": f"Sem resposta de {url} ({erro.__class__.__name__})"}


async def em_sequencia(cliente, qtd, valor):
    # Cliente-servidor comum. Conceito, UN4 S1 — latência somada, cerca de 0,8 s.
    inicio = time.perf_counter()
    estoque = await pedir(cliente, URL_ESTOQUE + "/consultar", {"item": "camiseta", "qtd": qtd})
    pagamento = await pedir(cliente, URL_PAGAMENTO + "/autorizar", {"valor": valor})
    return time.perf_counter() - inicio, estoque, pagamento


async def em_paralelo(cliente, qtd, valor):
    # Conceito, UN3 S4 — as duas esperas ao mesmo tempo. Cerca de 0,4 s.
    inicio = time.perf_counter()
    estoque, pagamento = await asyncio.gather(
        pedir(cliente, URL_ESTOQUE + "/consultar", {"item": "camiseta", "qtd": qtd}),
        pedir(cliente, URL_PAGAMENTO + "/autorizar", {"valor": valor}),
    )
    return time.perf_counter() - inicio, estoque, pagamento


@app.get("/health")
def health():
    return {"status": "up", "servico": "loja"}


@app.post("/vender")
async def vender(pedido: Pedido):
    async with httpx.AsyncClient() as cliente:
        if pedido.modo == "sequencia":
            gasto, estoque, pagamento = await em_sequencia(cliente, pedido.qtd, pedido.valor)
        else:
            gasto, estoque, pagamento = await em_paralelo(cliente, pedido.qtd, pedido.valor)
    venda = decidir(estoque, pagamento)
    print(
        f"loja modo={pedido.modo} qtd={pedido.qtd} valor={pedido.valor:.2f} "
        f"venda={venda} em {gasto:.2f} s",
        flush=True,
    )
    return {
        "modo": pedido.modo,
        "segundos": round(gasto, 2),
        "venda": venda,
        "estoque": estoque,
        "pagamento": pagamento,
    }
EOF
```

O Compose não é o paralelo. Conceito, UN4 S2 — ele só descreve os quatro contêineres: banco, estoque, pagamento e loja.

```bash
cat > ~/loja/docker-compose.yml << 'EOF'
# Conceito, UN4 S2 — contêineres. O paralelo está em loja/app.py, no gather.
services:
  banco:
    image: postgres:16-alpine
    container_name: banco
    restart: unless-stopped
    networks: [loja]
    environment:
      POSTGRES_USER: loja
      POSTGRES_PASSWORD: loja
      POSTGRES_DB: loja
    volumes:
      - ./postgres/init.sh:/docker-entrypoint-initdb.d/init.sh
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U loja -d loja"]
      interval: 2s
      timeout: 2s
      retries: 30
      start_period: 5s

  estoque:
    build: ./estoque
    container_name: estoque
    restart: unless-stopped
    networks: [loja]
    environment:
      ESTOQUE_DATABASE_URL: postgresql://loja:loja@banco:5432/estoque
    depends_on:
      banco:
        condition: service_healthy
    ports:
      - "8001:8000"

  pagamento:
    build: ./pagamento
    container_name: pagamento
    restart: unless-stopped
    networks: [loja]
    environment:
      PAGAMENTO_DATABASE_URL: postgresql://loja:loja@banco:5432/pagamento
    depends_on:
      banco:
        condition: service_healthy
    ports:
      - "8002:8000"

  loja:
    build: ./loja
    container_name: loja
    restart: unless-stopped
    networks: [loja]
    environment:
      ESTOQUE_URL: http://estoque:8000
      PAGAMENTO_URL: http://pagamento:8000
    depends_on:
      estoque:
        condition: service_started
      pagamento:
        condition: service_started
    ports:
      - "8000:8000"

networks:
  loja:
    name: loja-paralela
EOF
```

O script da medida também nasce aqui. Ele ainda não roda: os processos não estão no ar.

```bash
cat > ~/loja/pedidos.sh << 'EOF'
# Conceito, UN4 S1 — latência de uma venda, e speedup = T_sequencia / T_paralelo.
set -e
echo "Esperando estoque, pagamento e loja."
pronta=0
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8001/health >/dev/null \
    && curl -sf http://localhost:8002/health >/dev/null \
    && curl -sf http://localhost:8000/health >/dev/null; then
    pronta=1
    break
  fi
  sleep 1
done
if [ "$pronta" -ne 1 ]; then
  echo "A loja não respondeu. Confira: docker ps" >&2
  exit 1
fi
echo "Loja no ar."

medir() {
  echo >&2
  echo "== $1 ==" >&2
  corpo=$(curl -sS -X POST http://localhost:8000/vender \
    -H "Content-Type: application/json" \
    -d "$2")
  echo "$corpo" >&2
  echo >&2
  printf '%s' "$corpo" | sed -n 's/.*"segundos": *\([0-9.][0-9.]*\).*/\1/p'
}

t_seq=$(medir "1 camiseta, R$ 120 — uma consulta depois da outra" '{"qtd":1,"valor":120,"modo":"sequencia"}')
t_par=$(medir "1 camiseta, R$ 120 — as duas consultas juntas" '{"qtd":1,"valor":120,"modo":"paralelo"}')

echo
echo "Speedup = T_sequencia / T_paralelo"
awk -v s="$t_seq" -v p="$t_par" 'BEGIN {
  if (p + 0 == 0) { print "Sem tempo paralelo para dividir."; exit }
  printf "Speedup = %.2f / %.2f = %.2f\n", s, p, s / p
}'
echo "Speedup 2 seria o dobro da velocidade. O número fica perto de 2 porque as duas esperas andaram juntas."

medir "1 camiseta, R$ 900 — as duas consultas juntas" '{"qtd":1,"valor":900,"modo":"paralelo"}' >/dev/null
medir "10 camisetas, R$ 120 — as duas consultas juntas" '{"qtd":10,"valor":120,"modo":"paralelo"}' >/dev/null
EOF
chmod +x ~/loja/pedidos.sh
```

Os arquivos estão criados. O próximo passo é o único que sobe e mede.
