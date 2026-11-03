# Loja real — Killercoda

Dá para fazer a sessão inteira no Killercoda. O computador da sala não precisa de Docker nem de Python.

A pasta `~/loja` começa vazia. Os passos 1, 2 e 3 criam todos os arquivos: banco, estoque, pagamento, loja, Compose e o script da medida. O passo 4 é o que se faz depois que tudo foi criado:

```text
cd ~/loja
docker compose up --build -d
bash pedidos.sh
docker exec banco psql -U loja -d estoque -c "SELECT item, quantidade FROM saldo;"
docker stop pagamento
bash pedidos.sh
docker start pagamento
```

## Publicar o cenário

1. Repositório público no GitHub só com o conteúdo desta pasta. O `index.json` fica na raiz.
2. Em [killercoda.com](https://killercoda.com), conta gratuita, Creator, ligar o repositório.
3. Abrir "Loja: estoque e pagamento em paralelo" e clicar em Start.

A turma não usa GitHub. O repositório só publica o roteiro. A sessão dura cerca de uma hora, sem cartão.

A pasta `assets/` é a mesma cópia dos arquivos, para ler no material. Ela não é enviada para a sessão: o `index.json` não lista assets. Quem cria o código é quem está no terminal.

Não rode esta sessão ao mesmo tempo que `loja_terraform` na mesma máquina, se um dia o Compose for repetido fora do navegador. Os nomes `estoque`, `pagamento`, `loja` e `banco` são os mesmos.
