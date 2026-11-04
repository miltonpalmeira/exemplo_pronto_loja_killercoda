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
