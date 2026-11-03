# Loja: estoque e pagamento em paralelo

Tudo acontece neste navegador. A pasta `~/loja` começa vazia. Nada é copiado pronto.

A turma cria, nesta ordem: o banco, o estoque, o pagamento, a loja, o Compose e o script da medida. FastAPI é o contrato. Postgres é a memória de cada serviço. O `asyncio.gather` é a última função da loja.

O passo 4 é o que se faz depois que todos os arquivos existem: subir, medir, olhar a tabela e parar o pagamento.

A sessão dura cerca de uma hora e não pede cartão. O primeiro `docker compose up` baixa as imagens e leva alguns minutos. Por isso os arquivos nascem antes, e o sobe fica todo no último passo.
