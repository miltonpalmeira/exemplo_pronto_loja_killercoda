# Roteiro da aula — criar do zero e executar no Killercoda

Duas fases, nesta ordem.

1. Com a turma, no seu computador: criar o repositório, a pasta e cada arquivo. Ainda não abre o Killercoda.
2. Quando o código estiver completo: push, ligar o Killercoda, e pedir para a turma só executar.

A pasta que a turma cria é `loja/assets/`. É o projeto. O Killercoda copia essa pasta para a máquina da sessão. Os arquivos `index.json`, `intro.md`, `step1.md` e `step2.md` ficam ao lado, em `loja/`. Eles não são código da loja. São a página que o aluno vê, com os dois cliques de executar.

Árvore no fim:

```text
NOME-DO-REPO/
  loja/
    index.json
    intro.md
    foreground.sh
    step1.md
    step2.md
    finish.md
    assets/
      docker-compose.yml
      pedidos.sh
      postgres/init.sh
      estoque/requirements.txt
      estoque/Dockerfile
      estoque/app.py
      pagamento/requirements.txt
      pagamento/Dockerfile
      pagamento/app.py
      loja/requirements.txt
      loja/Dockerfile
      loja/app.py
```

Os três arquivos `.sh` precisam nascer com fim de linha LF. No editor, o canto inferior direito não pode ficar em CRLF. Se ficar, o Postgres recusa o `init.sh`.

## 1. Repositório vazio

No GitHub, crie um repositório público vazio. Sem README.

No computador:

```powershell
git clone https://github.com/USUARIO/NOME-DO-REPO.git
cd NOME-DO-REPO
mkdir loja\assets\postgres, loja\assets\estoque, loja\assets\pagamento, loja\assets\loja
```

Troque `USUARIO/NOME-DO-REPO` pelo repositório criado.

Se a aula for nesta pasta `loja_killercoda`, que já é um repositório, não clone de novo e não crie outra `loja` dentro dela. Os caminhos abaixo já são os desta pasta. Apague o arquivo correspondente antes de redigitar com a turma, se a ideia for escrever do zero na frente deles.

## 2. O que pedir para a turma criar

Um arquivo por vez. Grave, mostre, siga para o próximo. A ordem é a da aula: banco, estoque, pagamento, loja, Compose, medida.

### 2.1 `loja/assets/postgres/init.sh`

Peça este arquivo primeiro. Ele cria dois bancos no mesmo Postgres. O estoque não lê o limite. A loja não tem usuário aqui.

```bash
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
```

Confira o LF antes de salvar.

### 2.2 `loja/assets/estoque/requirements.txt`

```text
fastapi>=0.115
uvicorn>=0.32
psycopg[binary]>=3.2
```

### 2.3 `loja/assets/estoque/Dockerfile`

```dockerfile
# Conceito, UN4 S2 — contêiner.
# A imagem empacota este serviço. O mesmo arquivo sobe igual nesta máquina e no Killercoda.

# Imagem base com Python. O estoque não leva o código da loja nem o do pagamento.
FROM python:3.12-slim

# Pasta de trabalho dentro do contêiner.
WORKDIR /app

# Copia a lista de bibliotecas antes do código, para o build reaproveitar esta camada.
COPY requirements.txt .

# Instala o FastAPI e o Uvicorn dentro da imagem. A máquina da aula não precisa deles.
RUN pip install --no-cache-dir -r requirements.txt

# Copia o processo do estoque: a memória do saldo está neste arquivo.
COPY app.py .

# O processo escuta a porta 8000 dentro do contêiner.
EXPOSE 8000

# Conceito, UN3 S1 — falha parcial / prontidão.
# Enquanto /health não responder, o orquestrador trata o serviço como fora do ar.
HEALTHCHECK --interval=2s --timeout=1s --start-period=5s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# Conceito, UN1 — endereço.
# 0.0.0.0 escuta na rede do contêiner. Em 127.0.0.1 só quem está dentro dele alcançaria.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.4 `loja/assets/estoque/app.py`

Peça a função `consultar`. É `SELECT`, não `UPDATE`. O saldo continua 4.

```python
# Estoque — um processo e o banco dele: quantas camisetas existem.
#
# Conceito, UN3 S1 — memória privada:
# a tabela saldo está no banco "estoque". A loja não tem essa conexão.
# Ela manda uma mensagem e recebe TEM ou SEM_ESTOQUE.
#
# Conceito, UN3 S4 — serviço (SOA/REST):
# a função consultar é o contrato. Quem chamar recebe JSON, de qualquer linguagem.

import os
import time

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Conceito, UN3 S2 — nomeação. O nome do banco na rede é "banco". O IP fica com o Docker.
# Este processo só abre o banco estoque. A URL do pagamento não está aqui.
DATABASE_URL = os.environ["ESTOQUE_DATABASE_URL"]

# Conceito, UN4 S1 — latência.
# O Postgres desta máquina responde em milissegundos. 0,4 s segura o lugar
# da ida a um banco remoto, para a aula ver a soma das esperas e uma espera só.
TEMPO_ATENDIMENTO = 0.4


class Consulta(BaseModel):
    # Conceito, UN3 S4 — contrato da mensagem. O corpo tem o item e a quantidade.
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
    # Pronto só quando o banco responde. O Docker espera esta rota.
    with psycopg.connect(DATABASE_URL) as conexao:
        conexao.execute("SELECT 1")
    return {"status": "up", "servico": "estoque"}


@app.post("/consultar")
def consultar(pedido: Consulta):
    # A espera é deste processo. O pagamento espera no banco dele, no tempo dele.
    time.sleep(TEMPO_ATENDIMENTO)
    # Lê a tabela. Nenhuma linha faz UPDATE. Se baixasse, o segundo pedido
    # veria outro número e a aula misturaria o paralelo com a baixa.
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
```

### 2.5 `loja/assets/pagamento/requirements.txt`

O mesmo trio do estoque. Outro processo, outra imagem.

```text
fastapi>=0.115
uvicorn>=0.32
psycopg[binary]>=3.2
```

### 2.6 `loja/assets/pagamento/Dockerfile`

```dockerfile
# Conceito, UN4 S2 — contêiner. Imagem própria: o pagamento não enxerga o saldo do estoque.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

# A rota /health diz se este processo está no ar. Silêncio aqui é serviço fora.
HEALTHCHECK --interval=2s --timeout=1s --start-period=5s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# 0.0.0.0: a loja, em outro contêiner, precisa alcançar esta porta pela rede.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.7 `loja/assets/pagamento/app.py`

Peça `autorizar`. O limite é R$ 500. A loja não abre esta tabela.

```python
# Pagamento — um processo e o banco dele: o limite de R$ 500.
#
# Conceito, UN3 S1 — memória privada:
# a tabela limite está no banco "pagamento". Estoque e loja não conectam nela.
#
# Conceito, UN3 S4 — serviço (SOA/REST):
# o contrato é POST /autorizar. A resposta é APROVADO ou RECUSADO.

import os
import time

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Conceito, UN3 S2 — nomeação. Mesmo servidor de banco, outro database.
DATABASE_URL = os.environ["PAGAMENTO_DATABASE_URL"]

# Conceito, UN4 S1 — latência. O mesmo 0,4 s do estoque, de propósito.
# Em sequência a loja paga 0,4 + 0,4. Em paralelo paga um dos dois.
TEMPO_ATENDIMENTO = 0.4


class Autorizacao(BaseModel):
    # Conceito, UN3 S4 — contrato da mensagem. Só o valor viaja. O limite não vai na mensagem.
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
    # A ida ao banco deste serviço é a consulta. A espera completa os 0,4 s da aula.
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
```

### 2.8 `loja/assets/loja/requirements.txt`

A loja não leva `psycopg`. Ela não abre banco. Leva `httpx`, que manda as duas mensagens.

```text
fastapi>=0.115
uvicorn>=0.32
httpx>=0.27
```

### 2.9 `loja/assets/loja/Dockerfile`

```dockerfile
# Conceito, UN4 S2 — contêiner da loja. Só o cliente. Estoque e pagamento são outras imagens.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

HEALTHCHECK --interval=2s --timeout=1s --start-period=5s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# A loja fica no ar esperando POST /vender. Ela não inicia os outros dois processos.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.10 `loja/assets/loja/app.py`

Este é o arquivo do paralelo. Pare em `em_paralelo`: as duas mensagens saem no `asyncio.gather`. A loja espera um atendimento, cerca de 0,4 s. Em `em_sequencia` ela espera a soma, cerca de 0,8 s.

```python
# Loja — cliente dos dois serviços.
#
# Conceito, UN1 S2 — cliente-servidor:
# este processo não tem o saldo e não tem o limite. Ele pergunta.
#
# Conceito, UN3 S4 — paralelismo de tarefas com passagem de mensagem:
# consultar o estoque e autorizar o pagamento são tarefas diferentes.
# As duas mensagens saem juntas. A loja espera um atendimento, não a soma.
#
# O que este arquivo NÃO faz: não sobe o estoque nem o pagamento.
# Num projeto real esses processos já estão no ar. Quem os liga é o
# Docker, descrito pelo Terraform ou pelo Compose do Killercoda.

import asyncio
import os
import time

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Conceito, UN3 S2 — nomeação.
# A URL leva o nome do serviço (estoque, pagamento), não um IP fixo.
# O DNS da rede Docker troca o nome pelo endereço de agora.
# Se o contêiner ganhar outro IP, este nome continua certo.
# Fora do Docker, a variável de ambiente aponta para localhost e a porta publicada.
URL_ESTOQUE = os.environ.get("ESTOQUE_URL", "http://estoque:8000")
URL_PAGAMENTO = os.environ.get("PAGAMENTO_URL", "http://pagamento:8000")

# Conceito, UN3 S1 — falha parcial.
# 2 s é o limite de espera. O atendimento normal leva 0,4 s.
# Passou de 2 s, ou a conexão nem abriu: esta chamada volta FALHA.
# A loja não transforma silêncio em "tem camiseta" nem em "pode cobrar".
TIMEOUT_SEGUNDOS = 2.0


class Pedido(BaseModel):
    # Conceito, UN3 S4 — contrato de quem compra.
    # modo "sequencia" espera uma resposta e só então pede a outra.
    # modo "paralelo" manda as duas mensagens juntas. É o caminho do projeto real.
    qtd: int
    valor: float
    modo: str = "paralelo"


def decidir(estoque, pagamento):
    # Conceito, UN3 S1 — coordenação por mensagem.
    # CONFIRMADA só com TEM e APROVADO. FALHA, RECUSADO ou SEM_ESTOQUE barra a venda.
    if estoque.get("status") == "TEM" and pagamento.get("status") == "APROVADO":
        return "CONFIRMADA"
    return "NAO_CONFIRMADA"


async def pedir(cliente, url, corpo):
    # Conceito, UN1 S4 — passagem de mensagem. POST com JSON. A regra roda no outro processo.
    try:
        resposta = await cliente.post(url, json=corpo, timeout=TIMEOUT_SEGUNDOS)
        return resposta.json()
    except httpx.HTTPError as erro:
        # Conceito, UN3 S1 — falha parcial. Sem resposta não é um sim.
        return {"status": "FALHA", "mensagem": f"Sem resposta de {url} ({erro.__class__.__name__})"}


async def em_sequencia(cliente, qtd, valor):
    # Um cliente-servidor comum: pede, espera acabar, pede o próximo.
    # Conceito, UN4 S1 — latência somada. Cerca de 0,8 s (0,4 + 0,4).
    inicio = time.perf_counter()
    estoque = await pedir(cliente, URL_ESTOQUE + "/consultar", {"item": "camiseta", "qtd": qtd})
    pagamento = await pedir(cliente, URL_PAGAMENTO + "/autorizar", {"valor": valor})
    return time.perf_counter() - inicio, estoque, pagamento


async def em_paralelo(cliente, qtd, valor):
    # Conceito, UN3 S4 — paralelismo de tarefas. As duas mensagens saem juntas.
    # Conceito, UN3 S4 — laço de eventos: a loja espera a rede numa thread só.
    # Ela não ocupa dois núcleos. O trabalho simultâneo está nos outros dois processos.
    # Conceito, UN4 S1 — latência: o tempo cai para cerca de 0,4 s, um atendimento, não a soma.
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
    # Cada venda abre um cliente HTTP, manda as mensagens e fecha.
    # Num caixa com muita vazão o cliente seria reaproveitado (pool de conexões).
    # Conceito, UN4 S1 — vazão: aqui medimos a latência de UM pedido, que é o que o cliente sente.
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
```

### 2.11 `loja/assets/docker-compose.yml`

Peça por último entre os arquivos de serviço. O paralelo não está aqui. Aqui está quem sobe os quatro processos e o nome `estoque` / `pagamento` que a loja usa na URL. Usuário e senha da aula: `loja` / `loja`.

```yaml
# Conceito, UN4 S2 — contêineres.
# O banco guarda saldo e limite. O paralelo não está aqui.
# O paralelo está em loja/app.py, na função em_paralelo, no asyncio.gather.

services:
  # Conceito, UN3 S1 — dois databases no mesmo servidor: estoque e pagamento.
  # A loja não recebe a senha. Senha da aula, não é segredo de produção.
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

  # Conceito, UN3 S1 — memória privada. Este processo só abre o database estoque.
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
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 2s
      timeout: 3s
      retries: 30
      start_period: 10s

  # Conceito, UN3 S1 — outra memória. O limite fica no database pagamento.
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
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 2s
      timeout: 3s
      retries: 30
      start_period: 10s

  # Cliente. Conceito, UN3 S2 — nomeação: a URL usa o nome do serviço, não um IP.
  # A loja não tem DATABASE_URL. O dado chega pela mensagem.
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
        condition: service_healthy
      pagamento:
        condition: service_healthy
    ports:
      - "8000:8000"

networks:
  loja:
    name: loja-paralela
```

### 2.12 `loja/assets/pedidos.sh`

É o que a turma executa depois, no Killercoda. Quatro pedidos. No fim imprime o speedup. LF de novo.

```bash
# Mede os quatro pedidos com a loja já no ar.
# Conceito, UN4 S1 — latência: o campo segundos é o tempo de UMA venda.
# No fim, speedup = T_sequencia / T_paralelo, no mesmo pedido de 1 camiseta a R$ 120.
# Uso, na pasta loja_terraform: bash pedidos.sh

set -e

# Conceito, UN3 S1 — prontidão. O apply devolve o controle antes de o processo escutar.
echo "Esperando estoque, pagamento e loja. O /health do estoque e do pagamento só responde com o banco no ar."
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

# Imprime o pedido na tela e devolve só o número de segundos, para a conta do speedup.
medir() {
  echo >&2
  echo "== $1 ==" >&2
  # Conceito, UN1 S2 — cliente-servidor. Este curl é cliente da loja.
  # A loja, por sua vez, é cliente do estoque e do pagamento.
  corpo=$(curl -sS -X POST http://localhost:8000/vender \
    -H "Content-Type: application/json" \
    -d "$2")
  echo "$corpo" >&2
  echo >&2
  printf '%s' "$corpo" | sed -n 's/.*"segundos": *\([0-9.][0-9.]*\).*/\1/p'
}

# a) Uma mensagem depois da outra. A latência é a soma. O tempo fica em t_seq.
t_seq=$(medir "1 camiseta, R$ 120 — uma consulta depois da outra" '{"qtd":1,"valor":120,"modo":"sequencia"}')

# b) Conceito, UN3 S4 — paralelismo de tarefas. As duas mensagens juntas. O tempo fica em t_par.
t_par=$(medir "1 camiseta, R$ 120 — as duas consultas juntas" '{"qtd":1,"valor":120,"modo":"paralelo"}')

# Conceito, UN4 S1 — speedup. Mesmo pedido, dois modos. Speedup 2 seria o dobro da velocidade.
echo
echo "Speedup = T_sequencia / T_paralelo"
awk -v s="$t_seq" -v p="$t_par" 'BEGIN {
  if (p + 0 == 0) { print "Sem tempo paralelo para dividir."; exit }
  printf "Speedup = %.2f / %.2f = %.2f\n", s, p, s / p
}'
echo "Speedup 2 seria o dobro da velocidade. O número fica perto de 2 porque as duas esperas andaram juntas."

# c) O pagamento recusa. Paralelo não muda a regra: 900 não cabe em 500.
medir "1 camiseta, R$ 900 — as duas consultas juntas" '{"qtd":1,"valor":900,"modo":"paralelo"}' >/dev/null

# d) O estoque recusa. 10 não cabe no saldo 4. O saldo não foi baixado pelos pedidos anteriores.
medir "10 camisetas, R$ 120 — as duas consultas juntas" '{"qtd":10,"valor":120,"modo":"paralelo"}' >/dev/null
```

O código da aula acaba aqui. Os arquivos da seção 3 só fazem o Killercoda abrir a sessão.

## 3. Arquivos do cenário, depois do código

Crie estes seis na pasta `loja/`, não dentro de `assets/`. Sem o `index.json` dentro de `loja/`, a página do Killercoda fica em "No scenarios yet".

### 3.1 `loja/index.json`

```json
{
  "title": "Loja: estoque e pagamento em paralelo",
  "description": "A pasta da loja já chega pronta. Um comando sobe banco, estoque, pagamento e loja. Outro mede o paralelo. Sem cartão.",
  "details": {
    "intro": {
      "text": "intro.md",
      "foreground": "foreground.sh"
    },
    "steps": [
      {
        "title": "Subir e medir",
        "text": "step1.md"
      },
      {
        "title": "Parar o pagamento",
        "text": "step2.md"
      }
    ],
    "finish": {
      "text": "finish.md"
    },
    "assets": {
      "host01": [
        {"file": "docker-compose.yml", "target": "~/loja/"},
        {"file": "pedidos.sh", "target": "~/loja/", "chmod": "+x"},
        {"file": "postgres/init.sh", "target": "~/loja/postgres/", "chmod": "+x"},
        {"file": "estoque/Dockerfile", "target": "~/loja/estoque/"},
        {"file": "estoque/app.py", "target": "~/loja/estoque/"},
        {"file": "estoque/requirements.txt", "target": "~/loja/estoque/"},
        {"file": "pagamento/Dockerfile", "target": "~/loja/pagamento/"},
        {"file": "pagamento/app.py", "target": "~/loja/pagamento/"},
        {"file": "pagamento/requirements.txt", "target": "~/loja/pagamento/"},
        {"file": "loja/Dockerfile", "target": "~/loja/loja/"},
        {"file": "loja/app.py", "target": "~/loja/loja/"},
        {"file": "loja/requirements.txt", "target": "~/loja/loja/"}
      ]
    }
  },
  "backend": {
    "imageid": "ubuntu"
  }
}
```

### 3.2 `loja/intro.md`

```markdown
# Loja: estoque e pagamento em paralelo

A pasta `~/loja` já chega com banco, estoque, pagamento, loja e o Compose. Não há arquivo para criar.

O primeiro passo sobe tudo e mede. A sequência fica perto de 0,8 s. O paralelo fica perto de 0,4 s. O segundo passo para só o pagamento e mostra a venda que deixa de confirmar.

A primeira subida baixa as imagens e leva alguns minutos. A sessão dura cerca de uma hora e não pede cartão.
```

### 3.3 `loja/foreground.sh`

LF. Roda sozinho quando a sessão abre. Instala o Compose se a Ubuntu não tiver o plugin. Sem esse plugin, `docker compose up --build` responde `unknown flag: --build`.

```bash
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
```

### 3.4 `loja/step1.md`

O `{{exec}}` colado na cerca faz o Killercoda executar o bloco no clique.

~~~~markdown
# Subir e medir

`cd ~/loja` entra na pasta do projeto. O Compose só acha o `docker-compose.yml` estando aí.

`docker compose up` cria e liga banco, estoque, pagamento e loja. `--build` monta as três imagens Python antes de subir. `-d` devolve o terminal; o processo continua atrás.

`docker compose ps` lista o estado. Espere a coluna sair de `starting`.

A primeira vez baixa as imagens e leva alguns minutos. Clique:

```
cd ~/loja
docker compose up --build -d
docker compose ps
```{{exec}}

`bash pedidos.sh` espera o `/health` e faz os quatro pedidos. Clique quando o `ps` não mostrar mais `starting`:

```
cd ~/loja
bash pedidos.sh
```{{exec}}

O que tem de aparecer: a venda de 1 camiseta a R$ 120 confirma nas duas formas. A sequência fica perto de 0,8 s. O paralelo fica perto de 0,4 s. O speedup fica perto de 2. R$ 900 e 10 camisetas saem `NAO_CONFIRMADA`.
~~~~

### 3.5 `loja/step2.md`

~~~~markdown
# Parar o pagamento

`docker stop pagamento` para só esse contêiner. Banco, estoque e loja continuam. A loja não abre o banco: sem resposta do pagamento, a venda de R$ 120 deixa de confirmar.

```
docker stop pagamento
cd ~/loja
bash pedidos.sh
```{{exec}}

`docker start pagamento` liga de novo o mesmo contêiner, sem montar a imagem outra vez.

```
docker start pagamento
cd ~/loja
bash pedidos.sh
```{{exec}}

Se o primeiro pedido depois da volta sair `FALHA`, o processo ainda está abrindo. Clique o mesmo bloco outra vez.
~~~~

### 3.6 `loja/finish.md`

~~~~markdown
# O que ficou

O tempo caiu porque as duas mensagens andaram juntas. A venda só existe se as duas memórias concordam. Silêncio do pagamento não vira cobrança.

Para apagar os contêineres desta sessão:

```bash
cd ~/loja
docker compose down
```

A pasta `loja_terraform`, no material da disciplina, descreve o mesmo banco e os mesmos contêineres em Terraform, com o Docker da sua máquina. Também sem cartão. O `gather` continua na loja: ela não abre o banco.

Esta sessão do Killercoda acaba em cerca de uma hora e não guarda o que foi construído.
~~~~

## 4. Subir para o GitHub

Na pasta do repositório:

```powershell
git add .
git commit -m "Cenario da loja para o Killercoda."
git branch -M main
git push -u origin main
```

Se o `clone` já deixou `origin` e `main`, o `branch` e o `-u` na primeira vez bastam. Nos pushes seguintes:

```powershell
git add .
git commit -m "Atualiza a loja."
git push
```

## 5. Ligar o Killercoda

Entre em [killercoda.com](https://killercoda.com) com Github.

Se o nome do perfil for um código no estilo `8a45a10...`, troque. Só letra minúscula, número e hífen. Exemplo: `milton-santana`. Salve.

Abra [https://killercoda.com/creator/repository](https://killercoda.com/creator/repository). Preencha `usuario/nome-do-repo` e o branch `main`. Salve.

Na mesma página, copie a **Deploy Key**. No GitHub do repositório: **Settings → Deploy keys → Add deploy key**. Cole. Deixe só leitura. Salve.

Volte ao Killercoda e copie a **Payload URL** e o **Secret**. No GitHub: **Settings → Webhooks → Add webhook**.

- Payload URL: a URL copiada
- Content type: `application/json`
- Secret: o secret copiado

Salve. Se o primeiro push aconteceu antes deste webhook, avise de novo:

```powershell
git commit --allow-empty -m "Avisa o Killercoda."
git push
```

A lista de cenários é uma página, não um item de menu:

[https://killercoda.com/creator/scenarios](https://killercoda.com/creator/scenarios)

O título "Loja: estoque e pagamento em paralelo" aparece aí. Abra e clique em **Start** uma vez, antes da turma. A primeira abertura pode demorar enquanto o cache acompanha o push.

Se a página continuar em "No scenarios yet":

1. Em creator/repository o repositório salvo é o do push e o branch é `main`.
2. No GitHub, a primeira tela mostra a pasta `loja`, e dentro dela o `index.json`. Um `index.json` na raiz do repositório não conta.
3. Em **Settings → Webhooks** há uma entrega com visto verde.

O link do cenário é o que os alunos abrem. Cada um entra com a conta gratuita e clica em **Start**. A sessão dura cerca de uma hora e não pede cartão. A turma não mexe no GitHub.

## 6. O que pedir para eles executarem

Na sessão, a pasta `~/loja` já está preenchida com os arquivos da seção 2. Peça os comandos do passo **Subir e medir**.

Se `docker compose up --build -d` responder `unknown flag: --build`, esta Ubuntu tem o Docker e não tem o Compose. O `docker` leu o `--build` e recusou, porque essa opção é do Compose. Na sessão que já está aberta, rode isto uma vez. As próximas sessões instalam sozinhas, pelo `foreground.sh`.

```bash
mkdir -p ~/.docker/cli-plugins
curl -fsSL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
docker compose version
```

- `mkdir -p ~/.docker/cli-plugins` cria a pasta em que o Docker procura plugins. O `-p` não reclama se ela já existir.
- `curl -fsSL ... -o ...` baixa o programa Compose para essa pasta. `-f` falha se o arquivo não existir. `-sS` fica quieto, mas mostra erro. `-L` segue o redirecionamento do GitHub.
- `chmod +x` marca o arquivo como executável.
- `docker compose version` confere. Tem de imprimir a versão, não `unknown flag`.

Aí sim, subir. A primeira vez baixa as imagens e leva alguns minutos.

```bash
cd ~/loja
docker compose up --build -d
docker compose ps
```

- `cd ~/loja` entra na pasta do projeto. O Compose procura o `docker-compose.yml` na pasta atual.
- `docker compose up` lê esse arquivo, cria a rede e liga banco, estoque, pagamento e loja.
- `--build` monta as imagens do estoque, do pagamento e da loja a partir dos Dockerfiles, antes de ligar. O banco não tem Dockerfile: usa a imagem pronta `postgres:16-alpine`.
- `-d` significa detached. O comando devolve o terminal e os contêineres continuam rodando. Sem o `-d`, o terminal fica preso no log.
- `docker compose ps` lista os contêineres deste projeto e o estado de cada um.

Se a coluna ainda estiver `starting`, o processo ainda está abrindo. Rode de novo:

```bash
docker compose ps
```

Quando ninguém estiver `starting`, meça:

```bash
cd ~/loja
bash pedidos.sh
```

- `bash pedidos.sh` executa o script da medida. Ele espera o `/health` dos três serviços e manda os quatro pedidos. No fim imprime o speedup.

O que tem de aparecer:

| Pedido | Venda | segundos |
|---|---|---|
| 1 camiseta, R$ 120, sequência | CONFIRMADA | cerca de 0,8 |
| 1 camiseta, R$ 120, paralelo | CONFIRMADA | cerca de 0,4 |
| 1 camiseta, R$ 900, paralelo | NAO_CONFIRMADA | cerca de 0,4 |
| 10 camisetas, R$ 120, paralelo | NAO_CONFIRMADA | cerca de 0,4 |

O speedup impresso fica perto de 2.

No passo **Parar o pagamento**, se quiser mostrar a falha parcial:

```bash
docker stop pagamento
cd ~/loja
bash pedidos.sh
docker start pagamento
cd ~/loja
bash pedidos.sh
```

- `docker stop pagamento` para só o contêiner do pagamento. Banco, estoque e loja continuam. A camiseta a R$ 120 deixa de confirmar, porque a loja não recebe resposta.
- `bash pedidos.sh` mede de novo, agora com o pagamento parado.
- `docker start pagamento` liga de novo o mesmo contêiner. Não monta a imagem outra vez.
- O segundo `bash pedidos.sh` mede com os quatro no ar. A venda de R$ 120 volta a confirmar.

Se o primeiro pedido depois da volta sair `FALHA`, o processo ainda está abrindo. Rode outra vez:

```bash
bash pedidos.sh
```

No fim da sessão:

```bash
cd ~/loja
docker compose down
```

- `docker compose down` para e apaga os contêineres e a rede criados pelo `up`. A sessão não guarda isso.
