# Conceito, UN4 S2 — contêiner.
# A imagem empacota este serviço. O mesmo arquivo sobe igual nesta máquina e no Killercoda.

# Imagem base com Python. O estoque não leva o código da loja nem o do pagamento.
FROM python:3.12-slim

# Pasta de trabalho dentro do contêiner.
WORKDIR /app

# Copia a lista de bibliotecas antes do código, para o build reaproveitar esta camada.
COPY requirements.txt .

# Instala o FastAPI e o Uvicorn dentro da imagem. A máquina da aula não precisa deles.
RUN pip install --no-cache-dir -r requirements.txt

# Copia o processo do estoque: a memória do saldo está neste arquivo.
COPY app.py .

# O processo escuta a porta 8000 dentro do contêiner.
EXPOSE 8000

# Conceito, UN3 S1 — falha parcial / prontidão.
# Enquanto /health não responder, o orquestrador trata o serviço como fora do ar.
HEALTHCHECK --interval=2s --timeout=1s --start-period=5s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# Conceito, UN1 — endereço.
# 0.0.0.0 escuta na rede do contêiner. Em 127.0.0.1 só quem está dentro dele alcançaria.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
