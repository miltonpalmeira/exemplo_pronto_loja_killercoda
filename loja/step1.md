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
