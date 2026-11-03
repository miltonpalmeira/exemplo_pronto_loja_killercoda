# Conceito, UN4 S2 — contêiner da loja. Só o cliente. Estoque e pagamento são outras imagens.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

HEALTHCHECK --interval=2s --timeout=1s --start-period=5s --retries=20 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# A loja fica no ar esperando POST /vender. Ela não inicia os outros dois processos.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
