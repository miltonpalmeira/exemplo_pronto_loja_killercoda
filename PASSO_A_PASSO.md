# Passo a passo — publicar e rodar a loja no Killercoda

Tudo abaixo está na ordem. A parte do professor é feita uma vez. Na sessão, a pasta `~/loja` já chega pronta. A turma sobe e mede. Não digita o código.

## 1. Nome do perfil no Killercoda

Entre em [killercoda.com](https://killercoda.com) com **Github**.

Se aparecer um nome no estilo `8a45a10...` e o texto pedir outro nome, troque. Use só letra minúscula, número e hífen. Exemplo: `milton-santana`. Esse nome entra no endereço do cenário. Salve.

## 2. Repositório no GitHub

Crie um repositório público. O Killercoda não trata a raiz do repositório como cenário. O `index.json` fica numa pasta, por exemplo `loja/index.json`.

No computador, nesta pasta `loja_killercoda`:

```text
git init
git add .
git commit -m "Cenario da loja para o Killercoda."
git branch -M main
git remote add origin https://github.com/USUARIO/NOME-DO-REPO.git
git push -u origin main
```

Troque `USUARIO/NOME-DO-REPO` pelo repositório criado.

## 3. Ligar o repositório no Killercoda

Abra, já entrado na conta:

[https://killercoda.com/creator/repository](https://killercoda.com/creator/repository)

Preencha o repositório no formato `usuario/nome-do-repo` e o branch `main`. Salve.

## 4. Deploy Key e webhook

Na mesma página do Killercoda, copie a **Deploy Key**.

No GitHub, abra o repositório em **Settings → Deploy keys → Add deploy key**. Cole a chave. Deixe só leitura. Salve.

Volte ao Killercoda e copie a **Payload URL** e o **Secret**.

No GitHub, **Settings → Webhooks → Add webhook**.

- Payload URL: a URL copiada
- Content type: `application/json`
- Secret: o secret copiado

Salve o webhook.

## 5. Push de novo, para o webhook avisar o Killercoda

O primeiro push pode ter acontecido antes do webhook existir. Este segundo push é o aviso.

Nesta pasta:

```text
git commit --allow-empty -m "Avisa o Killercoda."
git push
```

O push não cria um menu chamado Creator Scenarios. A lista é uma página, e só abre com a conta já entrada:

[https://killercoda.com/creator/scenarios](https://killercoda.com/creator/scenarios)

O cenário "Loja: estoque e pagamento em paralelo" aparece nessa página. Abra e clique em **Start** uma vez, antes da turma.

Se a página abrir vazia, o commit no GitHub não basta. Confira, nesta ordem:

1. Em [https://killercoda.com/creator/repository](https://killercoda.com/creator/repository) o repositório está salvo como `usuario/nome-do-repo` e o branch é o mesmo do push (`main`).
2. No GitHub, a pasta `loja` aparece na primeira tela do repositório, e dentro dela está o `index.json`. O Killercoda ignora um `index.json` colocado na raiz do repositório. Por isso a página diz "No scenarios yet" mesmo com o commit sincronizado.
3. No GitHub, **Settings → Webhooks**, o webhook tem uma entrega recente com visto verde. Sem a Deploy Key e sem esse webhook, o Killercoda não lê o repositório.

O link dessa tela é o que os alunos abrem. Cada um entra com a conta gratuita e clica em **Start**. A sessão dura cerca de uma hora e não pede cartão. A turma não usa o GitHub.

## 6. Na sessão: subir

A máquina é uma Ubuntu com Docker. No início, o Killercoda copia `loja/assets/` para `~/loja`. Banco, estoque, pagamento, loja, Compose e `pedidos.sh` já estão lá.

O passo **Subir e medir** tem dois blocos. Clicar no bloco executa. O primeiro sobe. A primeira vez baixa as imagens e leva alguns minutos.

```bash
cd ~/loja
docker compose up --build -d
docker compose ps
```

Se a coluna ainda estiver `starting`, rode de novo:

```bash
docker compose ps
```

O segundo bloco mede. Sequência perto de 0,8 s. Paralelo perto de 0,4 s. Speedup perto de 2.

```bash
cd ~/loja
bash pedidos.sh
```

O que tem de aparecer:

| Pedido | Venda | segundos |
|---|---|---|
| 1 camiseta, R$ 120, sequência | CONFIRMADA | cerca de 0,8 |
| 1 camiseta, R$ 120, paralelo | CONFIRMADA | cerca de 0,4 |
| 1 camiseta, R$ 900, paralelo | NAO_CONFIRMADA | cerca de 0,4 |
| 10 camisetas, R$ 120, paralelo | NAO_CONFIRMADA | cerca de 0,4 |

A consulta não deu `UPDATE`. A quantidade continua 4 e o limite continua 500.

```bash
docker exec banco psql -U loja -d estoque -c "SELECT item, quantidade FROM saldo;"
docker exec banco psql -U loja -d pagamento -c "SELECT id, valor FROM limite;"
```

Pare só o pagamento. A camiseta a R$ 120 deixa de confirmar. Ligue de novo e meça outra vez.

```bash
docker stop pagamento
bash pedidos.sh
docker start pagamento
bash pedidos.sh
```

Se o primeiro pedido depois da volta sair `FALHA`, o processo ainda está abrindo. Rode outra vez:

```bash
bash pedidos.sh
```

No fim da sessão, apague os contêineres:

```bash
cd ~/loja
docker compose down
```
