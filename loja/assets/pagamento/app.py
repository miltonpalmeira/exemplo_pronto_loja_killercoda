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
