# Parar o pagamento

A loja não abre o banco. Se o pagamento some, a venda de R$ 120 deixa de confirmar. Clique:

```
docker stop pagamento
cd ~/loja
bash pedidos.sh
```{{exec}}

Ligue de novo e meça outra vez:

```
docker start pagamento
cd ~/loja
bash pedidos.sh
```{{exec}}

Se o primeiro pedido depois da volta sair `FALHA`, o processo ainda está abrindo. Clique o mesmo bloco outra vez.
