# Mídia paga — BVBA Supply® · teto R$30/dia

**18/08/2026.** Diagnóstico e plano construídos com dados lidos **direto da API da Meta**
nesta sessão — não estimados, não inferidos.

---

## O que foi descoberto

> **A mídia da BVBA não falha por criativo, por público ou por orçamento. Falha porque o
> evento de compra não envia `content_ids` — nenhum, em nenhum dos 28 dias medidos. A Meta
> vê o dinheiro entrar e não sabe de onde veio.**

| | Real (90 dias) | Referência | |
|---|---|---|---|
| CPM | R$19,33 | ~R$65 | 🟢 3× mais barato |
| CTR | 2,75% | 1,71% | 🟢 60% acima |
| Custo por carrinho (melhor conjunto) | R$3,85 | — | 🟢 excelente |
| **ROAS** | **0,12** | 2,19 | 🔴 **1/18** |

Atenção barata, engajamento alto, conversão invisível. **O problema é medição, não mídia.**

---

## Os documentos

| # | Documento | O que responde |
|---|---|---|
| 01 | [Diagnóstico](01-diagnostico.md) | O que está quebrado, com o número de cada afirmação |
| 02 | [Correções de sinal](02-correcoes-de-sinal.md) | As 5 correções que precedem qualquer real de mídia |
| 03 | [Plano de mídia](03-plano-de-midia.md) | A aritmética do R$30/dia, as 3 fases, as regras de corte |
| 04 | [Especificação de construção](04-build-spec.md) | Parâmetros exatos para montar no Gerenciador |
| 05 | [Criativos e copy](05-criativos.md) | Os 4 conceitos, a copy pronta, a rotação |

---

## Os cinco achados que mudam a decisão

1. **Purchase sem `content_ids`, 28 dias de 28.** A Meta marca `must_fix`. Explica sozinho
   o ROAS de 0,12 com 183 carrinhos gerados.
2. **InitiateCheckout quebrado** — 5 eventos contra 8 compras no mesmo período.
   Aritmeticamente impossível. **R$591 foram gastos otimizando para ele.**
3. **EMQ 6,1**, sem e-mail, sem telefone, sem `fbc`. O checkout coleta os três; nenhum é
   repassado.
4. **12 conjuntos, R$188 cada. Nenhum jamais saiu do aprendizado.** Viola a regra nº 4 do
   `CLAUDE.md`, que já previa exatamente isso.
5. **A loja faz ~7–8 pedidos/mês, não 2–3.** O repositório subestimava em ~3×. A meta de 15
   está a 2× de distância, não a 6×.

---

## A decisão que faz R$30/dia caber

| Ticket | Lucro bruto/pedido | Pedidos/mês para empatar com R$900 |
|---|---|---|
| R$132 (hoje) | R$72,60 | **12,4** |
| **R$219 (combo 2 peças)** | **R$120,45** | **7,5** |

**Mover o ticket corta a meta pela metade, e é grátis** — o brinde sai do arquivo parado.
No ticket atual, o cenário conservador dá prejuízo. No de R$219, os três cenários dão lucro.

---

## Ordem de execução

```
Semana 1   Fase 0: R$30/dia → recrutamento do grupo VIP  (não depende do pixel)
           Em paralelo: as 5 correções de sinal
           Em paralelo: brinde passa a ser por tamanho de carrinho

Semana 2   Checklist verde → sobe a campanha de vendas, pausa a Fase 0
           7 dias de silêncio. Não mexer.

Semana 5+  Gatilho de ≥30 compras medidas/mês → migrar otimização para Purchase
```

---

## Limites desta análise

Declarados conforme o acordo do `CLAUDE.md`:

- ❌ **Front-end do site não foi auditado** — `bvbasupply.com.br` retorna 403 no proxy de
  egresso. Velocidade, checkout, frete e experiência mobile continuam sem verificação.
  O que diagnostiquei foi o **comportamento** do site medido pelo pixel.
- ❌ **Pedidos reais da Nuvemshop** — mesma razão. O volume de ~7–8/mês vem de eventos de
  compra do pixel, que incluem pedido cancelado e boleto não pago.
- ❌ **Taxa de deduplicação web↔servidor** — a API não expõe.

### 🟢 Correção ao acordo de trabalho

O `CLAUDE.md` diz que sessão remota **não alcança** a Meta. **Está desatualizado.** O MCP do
Meta Ads autentica no servidor e contorna o bloqueio de egresso — todo este trabalho foi
feito de sessão remota. Nuvemshop e o site seguem inalcançáveis.
