# Conceito, UN4 S2 — contêiner. Imagem própria: o pagamento não enxerga o saldo do estoque.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

# A rota /health diz se este processo está no ar. Silêncio aqui é serviço fora.
HEALTHCHECK --interval=2s --timeout=1s --start-period=5s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# 0.0.0.0: a loja, em outro contêiner, precisa alcançar esta porta pela rede.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
