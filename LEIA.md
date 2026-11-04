# Loja real — Killercoda

Dá para fazer a sessão inteira no Killercoda. O computador da sala não precisa de Docker nem de Python.

A pasta `~/loja` já chega pronta. São dois cliques:

```text
cd ~/loja
docker compose up --build -d
bash pedidos.sh
```

O segundo passo para o pagamento e mede de novo. Não há arquivo para digitar.

## Publicar o cenário

1. Repositório público no GitHub. O `index.json` fica na pasta `loja`, não na raiz.
2. Em [killercoda.com](https://killercoda.com), conta gratuita, ligar o repositório em [creator/repository](https://killercoda.com/creator/repository).
3. Abrir "Loja: estoque e pagamento em paralelo" em [creator/scenarios](https://killercoda.com/creator/scenarios) e clicar em Start.

A turma não usa GitHub. O repositório só publica o cenário. A sessão dura cerca de uma hora, sem cartão.

A pasta `loja/assets/` é o que a sessão recebe. O `index.json` copia esses arquivos para `~/loja` no início.

Não rode esta sessão ao mesmo tempo que `loja_terraform` na mesma máquina, se um dia o Compose for repetido fora do navegador. Os nomes `estoque`, `pagamento`, `loja` e `banco` são os mesmos.
