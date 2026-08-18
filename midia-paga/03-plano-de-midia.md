# 03 — Plano de mídia paga · teto R$30/dia

**18/08/2026** · Horizonte de 90 dias · Conta `321768910427826`

---

## A aritmética que governa tudo

R$30/dia = **R$900/mês**. Margem bruta ~55%.

| Ticket | Lucro bruto/pedido | Pedidos/mês só para **empatar** com R$900 |
|---|---|---|
| R$132 (1 peça — hoje) | R$72,60 | **12,4** |
| **R$219 (2 peças)** | **R$120,45** | **7,5** |
| R$299 (3 peças) | R$164,45 | 5,5 |

> **CAC precisa ser menor que o lucro bruto de 30 dias.** Com ticket de R$132, R$30/dia exige
> 12,4 pedidos/mês só para não perder dinheiro. Com o combo de 2 peças, exige 7,5.
>
> **A mudança de ticket corta a meta pela metade. É a alavanca mais barata do plano — e é grátis.**

A loja faz ~7–8 pedidos/mês hoje (medido no pixel, seção 10 do diagnóstico). Ou seja:
**no ticket atual, R$30/dia não fecha a conta. No ticket de R$219, fecha com folga.**

Por isso a decisão nº 1 deste plano não é de mídia. É de oferta.

---

## Decisão nº 1 — o brinde passa a ser destravado por tamanho de carrinho

Já é a recomendação do [`PLANO.md`](../PLANO.md) (Motor 2) e do plano de 02/08. Este plano
apenas a torna **pré-requisito da mídia**, não item paralelo.

| | Por posição na fila (hoje) | **Por tamanho de carrinho** |
|---|---|---|
| Quem controla | a hora em que a pessoa comprou | **o cliente** |
| Verificável antes de comprar | não | **sim** |
| Efeito no ticket | neutro | **R$132 → R$219** |
| Custo marginal | — | **~zero** (arquivo parado, ~114 peças) |

**Mecânica:** a partir de **2 peças**, o pedido leva 1 peça do arquivo à escolha.

Isto respeita a **regra nº 2 do `CLAUDE.md`** — é bônus a 100%, não desconto de vitrine.
Desconto de 10–20% na vitrine pública só corta margem de quem já ia comprar.

**O que limita:** estoque de brinde. Hoje são 9 bonés. O `PLANO.md` já aponta que os ~R$900/mês
deveriam repor esse estoque — com a mídia ligada, **repor brinde continua sendo pré-requisito**,
porque é ele que sustenta o ticket que faz a mídia caber.

---

## A arquitetura: uma campanha, um conjunto

**Regra nº 4 do `CLAUDE.md`:** *"Com R$30/dia, uma campanha e um conjunto. Dividir em três
impede que qualquer um saia do aprendizado."*

O diagnóstico mostrou o custo de ter violado isso: **12 conjuntos, R$188 cada, nenhum jamais
saiu do aprendizado.**

R$30/dia num conjunto único = R$900/mês concentrados. Ainda é pouco para os 50 eventos/semana
ideais, mas é **a única configuração em que o aprendizado é sequer possível.**

> **Retargeting não ganha conjunto próprio.** Não há volume para sustentar dois. O reimpacto
> entra pelo **Advantage+ Audience**, que já faz isso dentro do conjunto único — e foi
> exatamente a configuração dos dois melhores conjuntos da conta (CJ6 e CJ9, R$3,80/ATC).

**Quando abrir um segundo conjunto:** só acima de **R$60/dia**. Abaixo disso, dividir é
garantir que nenhum dos dois aprenda.

---

## As três fases

### FASE 0 · Dias 1–7 — enquanto o sinal é consertado

**O orçamento não fica parado.** Enquanto as cinco correções de
[`02-correcoes-de-sinal.md`](02-correcoes-de-sinal.md) rodam, R$30/dia vão para a única frente
que **não depende do pixel**: recrutamento para o grupo VIP no WhatsApp.

| | |
|---|---|
| Objetivo | Tráfego (cliques no link) → link direto do grupo |
| Por que funciona sem pixel | a conversão acontece no WhatsApp, não no site |
| Custo comprovado | **R$0,40/clique** (CJ18: R$173,27 → 429 cliques, CPM R$7,54) |
| Meta em 7 dias | R$210 → ~525 cliques → **50–80 novos membros** |
| Grupo | 218 → ~280 |

É o clique mais barato que a conta já produziu, e alimenta o canal que o `PLANO.md` identifica
como o lugar onde a venda de fato fecha.

**Fase 0 termina quando os 5 itens do checklist de liberação estiverem verdes** — não por data.

---

### FASE 1 · Dias 8–35 — vendas, otimizando AddToCart

**Uma campanha. Um conjunto. R$30/dia.**

#### Por que AddToCart e não Purchase

| Evento | Volume/mês no site | Serve para otimizar? |
|---|---|---|
| ViewContent | ~586 | alto demais no funil |
| **AddToCart** | **~55** | ✅ **o único com massa utilizável** |
| InitiateCheckout | ~5 | ❌ quebrado |
| Purchase | ~8 | ❌ volume baixo demais para sair do aprendizado |

Com 8 compras/mês, otimizar para Purchase deixa o conjunto preso no aprendizado
indefinidamente. AddToCart tem ~7× mais volume e, **depois da correção nº 1**, carrega
`content_ids` — o otimizador consegue trabalhar.

Foi também o que empiricamente funcionou: os dois conjuntos de melhor custo por ATC da conta
(R$3,85 e R$3,80) otimizavam ATC ou tinham público de ATC.

#### Projeção — três cenários

Base: custo por ATC entre R$3,85 (melhor conjunto histórico) e R$12,31 (média da conta
fragmentada). Consolidado, o realista é **R$6–8**.

| Cenário | ATC/mês | ATC→Compra | Pedidos | Receita a R$219 | ROAS | Lucro bruto − R$900 |
|---|---|---|---|---|---|---|
| Conservador | 100 (R$9/ATC) | 10% | 10 | R$2.190 | 2,4 | **+R$304** |
| **Base** | **128 (R$7/ATC)** | **12%** | **15** | **R$3.285** | **3,7** | **+R$907** |
| Otimista | 160 (R$5,60/ATC) | 14,5% | 23 | R$5.037 | 5,6 | **+R$1.870** |

**No ticket antigo de R$132, o cenário conservador dá prejuízo de R$174.**
No de R$219, os três cenários dão lucro. É a mesma tabela que justifica a decisão nº 1.

> ATC→Compra de 14,5% é a taxa medida no site (8 compras / 55 carrinhos, 28 dias). Usei 10–12%
> nos cenários mais fechados porque tráfego pago converte abaixo do misto.

---

### FASE 2 · Dias 36–90 — migrar para Purchase e escalar

**Gatilho de migração:** ≥30 compras medidas/mês com `content_ids` por 2 semanas seguidas.

Aí sim:
1. Trocar a otimização do conjunto de **AddToCart → Purchase**
2. Testar **Advantage+ Sales** como campanha espelho (referência: +22% ROAS, −11,7% CPA)
3. Só então avaliar subir de R$30/dia

**Regra de escala:** só aumentar orçamento após **7 dias seguidos** de ROAS ≥ 2,0. Aumentar
em **+20% a cada 4 dias**, nunca dobrar — salto de orçamento reinicia o aprendizado e joga
fora tudo que o conjunto acumulou.

---

## Painel semanal — cinco números, toda segunda

| # | Métrica | Hoje | Meta 90 dias | Onde |
|---|---|---|---|---|
| 1 | **EMQ do Purchase** | não pontuado | **≥ 8,0** | Gerenciador de Eventos |
| 2 | **Custo por AddToCart** | R$12,31 | **≤ R$8,00** | Gerenciador de Anúncios |
| 3 | **Ticket médio** | R$132 | **R$219** | Nuvemshop |
| 4 | **Pedidos/mês** | ~7–8 | **15+** | Nuvemshop |
| 5 | **ROAS (7d clique)** | 0,12 | **≥ 2,0** | Gerenciador de Anúncios |

O nº 1 é o único que precisa estar verde antes de todos os outros importarem.

---

## Regras de corte — decididas antes, não no calor

| Situação | Ação | Prazo |
|---|---|---|
| Custo por ATC > R$15 por 5 dias seguidos | trocar criativo, **não** mexer no público | dia 5 |
| ROAS < 1,0 com ≥20 compras medidas | pausar e reler o sinal | quinzenal |
| Frequência > 3,5 | rotacionar criativo | semanal |
| CTR cai >20% em 14 dias | fadiga — subir criativo novo | semanal |
| EMQ do Purchase cai < 7,0 | **pausar mídia** e consertar | imediato |
| 30 dias sem bater 10 pedidos/mês | voltar 100% ao motor 1-a-1 do `PLANO.md` | dia 30 |

**Sete dias de silêncio.** Não mexer no conjunto durante os 7 primeiros dias, por pior que
pareça. Toda edição reinicia o aprendizado. Esta é a regra mais violada e a mais cara.

---

## Como isto conversa com o `PLANO.md`

O `PLANO.md` v2 pausa a mídia e condiciona o retorno a três gatilhos. Você decidiu religar —
é sua chamada, e este plano a executa. Vale registrar honestamente onde os dois se encontram:

| Gatilho do `PLANO.md` | Situação real | Como este plano trata |
|---|---|---|
| 15+ pedidos/mês por canal próprio, 2 meses | ~7–8/mês (3× mais que a inferência antiga) | não atingido — mas a distância é 2×, não 6× |
| **EMQ ≥ 7 com CAPI ativa e deduplicada** | CAPI ✅ · EMQ 6,1 ❌ | **virou a Fase 0 — pré-requisito absoluto** |
| Ticket médio ≥ R$200 | R$132 | **virou a decisão nº 1 — pré-requisito** |

**Dois dos três gatilhos foram transformados em pré-requisito executável em vez de barreira
de espera.** O terceiro (volume) melhora sozinho quando os outros dois fecham.

**O que não muda:** o motor 1-a-1 e a reativação da base seguem sendo o de maior retorno por
real investido. Mídia paga aqui **amplifica** esse motor — não o substitui. As 40 conversas
por semana continuam sendo a métrica operacional nº 1 da marca.
