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
