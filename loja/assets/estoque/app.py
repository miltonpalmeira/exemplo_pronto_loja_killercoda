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
