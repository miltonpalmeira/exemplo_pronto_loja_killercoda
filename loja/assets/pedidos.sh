# Mede os quatro pedidos com a loja já no ar.
# Conceito, UN4 S1 — latência: o campo segundos é o tempo de UMA venda.
# No fim, speedup = T_sequencia / T_paralelo, no mesmo pedido de 1 camiseta a R$ 120.
# Uso, na pasta loja_terraform: bash pedidos.sh

set -e

# Conceito, UN3 S1 — prontidão. O apply devolve o controle antes de o processo escutar.
echo "Esperando estoque, pagamento e loja. O /health do estoque e do pagamento só responde com o banco no ar."
pronta=0
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8001/health >/dev/null \
    && curl -sf http://localhost:8002/health >/dev/null \
    && curl -sf http://localhost:8000/health >/dev/null; then
    pronta=1
    break
  fi
  sleep 1
done
if [ "$pronta" -ne 1 ]; then
  echo "A loja não respondeu. Confira: docker ps" >&2
  exit 1
fi
echo "Loja no ar."

# Imprime o pedido na tela e devolve só o número de segundos, para a conta do speedup.
medir() {
  echo >&2
  echo "== $1 ==" >&2
  # Conceito, UN1 S2 — cliente-servidor. Este curl é cliente da loja.
  # A loja, por sua vez, é cliente do estoque e do pagamento.
  corpo=$(curl -sS -X POST http://localhost:8000/vender \
    -H "Content-Type: application/json" \
    -d "$2")
  echo "$corpo" >&2
  echo >&2
  printf '%s' "$corpo" | sed -n 's/.*"segundos": *\([0-9.][0-9.]*\).*/\1/p'
}

# a) Uma mensagem depois da outra. A latência é a soma. O tempo fica em t_seq.
t_seq=$(medir "1 camiseta, R$ 120 — uma consulta depois da outra" '{"qtd":1,"valor":120,"modo":"sequencia"}')

# b) Conceito, UN3 S4 — paralelismo de tarefas. As duas mensagens juntas. O tempo fica em t_par.
t_par=$(medir "1 camiseta, R$ 120 — as duas consultas juntas" '{"qtd":1,"valor":120,"modo":"paralelo"}')

# Conceito, UN4 S1 — speedup. Mesmo pedido, dois modos. Speedup 2 seria o dobro da velocidade.
echo
echo "Speedup = T_sequencia / T_paralelo"
awk -v s="$t_seq" -v p="$t_par" 'BEGIN {
  if (p + 0 == 0) { print "Sem tempo paralelo para dividir."; exit }
  printf "Speedup = %.2f / %.2f = %.2f\n", s, p, s / p
}'
echo "Speedup 2 seria o dobro da velocidade. O número fica perto de 2 porque as duas esperas andaram juntas."

# c) O pagamento recusa. Paralelo não muda a regra: 900 não cabe em 500.
medir "1 camiseta, R$ 900 — as duas consultas juntas" '{"qtd":1,"valor":900,"modo":"paralelo"}' >/dev/null

# d) O estoque recusa. 10 não cabe no saldo 4. O saldo não foi baixado pelos pedidos anteriores.
medir "10 camisetas, R$ 120 — as duas consultas juntas" '{"qtd":10,"valor":120,"modo":"paralelo"}' >/dev/null
