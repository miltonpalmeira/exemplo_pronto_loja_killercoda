# Depois de criar os arquivos

Os passos 1, 2 e 3 só gravaram arquivos. Nada está no ar. Daqui para a frente é só executar.

Sobe o banco e os três serviços. A primeira vez baixa as imagens e leva alguns minutos. Conceito, UN4 S2 — contêiner: o Compose empacota o que a turma criou.

```bash
cd ~/loja
docker compose up --build -d
docker compose ps
```

Espere a coluna de saúde do banco, do estoque e do pagamento. Se ainda estiver `starting`, rode o `ps` de novo.

Meça. Sequência perto de 0,8 s. Paralelo perto de 0,4 s. Speedup perto de 2.

```bash
bash pedidos.sh
```

| Pedido | Venda | segundos |
|---|---|---|
| 1 camiseta, R$ 120, sequência | CONFIRMADA | cerca de 0,8 |
| 1 camiseta, R$ 120, paralelo | CONFIRMADA | cerca de 0,4 |
| 1 camiseta, R$ 900, paralelo | NAO_CONFIRMADA | cerca de 0,4 |
| 10 camisetas, R$ 120, paralelo | NAO_CONFIRMADA | cerca de 0,4 |

A tabela continua 4. A consulta não deu `UPDATE`.

```bash
docker exec banco psql -U loja -d estoque -c "SELECT item, quantidade FROM saldo;"
docker exec banco psql -U loja -d pagamento -c "SELECT id, valor FROM limite;"
```

Pare só o pagamento. Conceito, UN3 S1 — falha parcial. A camiseta a R$ 120 deixa de confirmar.

```bash
docker stop pagamento
bash pedidos.sh
docker start pagamento
bash pedidos.sh
```

Se o primeiro pedido depois da volta sair `FALHA`, rode `bash pedidos.sh` outra vez.
