# Subir e medir

Clique no bloco. Ele sobe o banco, o estoque, o pagamento e a loja. A primeira vez baixa as imagens e leva alguns minutos.

```
cd ~/loja
docker compose up --build -d
docker compose ps
```{{exec}}

Quando a coluna de estado deixar de ficar em `starting`, clique neste bloco. Ele espera o `/health` e mede os quatro pedidos.

```
cd ~/loja
bash pedidos.sh
```{{exec}}

O que tem de aparecer: a venda de 1 camiseta a R$ 120 confirma nas duas formas. A sequência fica perto de 0,8 s. O paralelo fica perto de 0,4 s. O speedup fica perto de 2. R$ 900 e 10 camisetas saem `NAO_CONFIRMADA`.
