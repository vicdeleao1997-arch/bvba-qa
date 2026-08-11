# Plano de Marketing 360 — BVBA Supply®
### Liquidar o arquivo + lançar o AW 2026 com ROAS saudável a R$30/dia

**Data:** 11 de agosto de 2026
**Marca:** BVBA Supply® — *Supplying good trips!* · CNPJ 41.242.625/0001-47
**Loja:** bvbasupply.com.br (Nuvemshop) · **Instagram:** [@bvbasupply](https://www.instagram.com/bvbasupply/) (6.290 seguidores)
**Conta de anúncios:** CA - BVBA SUPPLY (321768910427826)

---

## Índice

| Documento | Conteúdo |
|---|---|
| **README.md** (este) | Diagnóstico, estratégia central, arquitetura de campanha, KPIs |
| [`01-ofertas.md`](01-ofertas.md) | As 4 ofertas prontas, com preços, ancoragem e matemática |
| [`02-meta-ads.md`](02-meta-ads.md) | Estrutura de campanha, segmentação, regras de otimização e escala |
| [`03-criativos-e-copy.md`](03-criativos-e-copy.md) | 5 ângulos, copy pronta dos anúncios, roteiros de Reels |
| [`04-crm-whatsapp-email.md`](04-crm-whatsapp-email.md) | Scripts de reativação da base, sequências e automações |
| [`05-calendario-8-semanas.md`](05-calendario-8-semanas.md) | Cronograma dia a dia, com responsáveis e gatilhos |
| [`06-medicao-e-checklist.md`](06-medicao-e-checklist.md) | Setup de Pixel/CAPI, KPIs, checklist bloqueante de lançamento |
| [`07-fontes-e-proveniencia.md`](07-fontes-e-proveniencia.md) | **Leia antes de agir nos números.** Classifica cada dado por origem — oficial, terceiro ou estimativa minha |

---

## 1. Diagnóstico — o que o ecossistema mostra

Levantamento feito a partir do Drive da BVBA, do Gmail operacional, do site e do Instagram.

### 1.1 O que existe hoje

**Ativos fortes (subaproveitados):**

| Ativo | Estado | Valor não capturado |
|---|---|---|
| Base de ~500+ telefones de clientes (`Fonte clientes BVBA 04.2024.csv`) | Parada desde abr/2024 | **Maior ativo da marca.** Custo de contato R$0, taxa de conversão de base morna 5–15× a de tráfego frio |
| Instagram @bvbasupply — 6.290 seguidores, 225 posts | Ativo | Audiência já construída, sem oferta clara apontada para ela |
| Coleção AW 2026 "Drop 2" — 11 SKUs com ficha técnica fechada | Produção/edição | Shooting já realizado em 25/07 (pasta `SHOOTING_25/07_V2`, edição em andamento) |
| Estoque de arquivo 2021–2023 | Parado | ~114 peças na última contagem estruturada (`Controle Estoque`) — capital imobilizado |
| Loja Nuvemshop + Mercado Pago + certificado e-CNPJ A1 (emitido jun/2026) | Operacional | Emissão de NF-e destravada, pronta para escalar |
| Parceria Arka Shop | Lançamento iminente | Canal de distribuição adicional sem custo de mídia |

**A coleção nova (AW 2026 — Outono/Inverno):**

- `MLT-001` Moletom Canguru Oversized — Marrom Café (estampa Dalí/café)
- `CJW-002` **Calça/Jorts Jeans Oversized Wide — Preto, conversível por zíper** ← peça-herói
- `JRT-003` Jorts Jeans Oversized Wide — Preto
- `CMS-004` a `CMS-011` — 8 Camisetas Oversized Boxy (Off-White, Azul Escuro, Marrom Café, Cinza Chumbo)
- Bonés: Fivepanel Logo, Blueberry, Nippon Dad Hat · Chaveiro
- Estampas: gato BVBA, museu, sakura, café, "Luzes do Irreal"

**O estoque encalhado (baseline da última contagem estruturada):**

| Peça | Un. | Peça | Un. |
|---|---|---|---|
| Fivepanel Logo Black | 23 | Tee Get Higher Telha | 14 |
| Tee Get Higher Black | 22 | Tee Next Level Black | 13 |
| Tee Logo White | 18 | Tee Logo Black | 8 |
| Tsunobag Moss Green | 7 | Tee Stay Negative Off-White | 6 |
| Tsunobag Black | 2 | Moletom BVBAFLIES | 1 |
| | | **Total** | **~114 peças** |

> ⚠️ Esta contagem é da planilha `Controle Estoque` (Coleção 01/2023) e **precisa ser reconferida** — houve a coleção "Luzes do Irreal" (dez/2025) e uma "SALE Janeiro 26" depois disso. O primeiro item do checklist é recontar. A estratégia abaixo funciona com qualquer número; só as quantidades de bônus mudam.

### 1.2 O problema central

A conta de Meta Ads vem gastando de forma consistente: **R$759 (jun) · R$385 (jun) · R$759 (jul) · R$350 (jul) · R$759 (ago)** — cerca de **R$1.100/mês**, ou ~R$36/dia. Esses valores são de recibos que identificam nominalmente a conta *CA - BVBA SUPPLY (321768910427826)*.

> **Correção de uma versão anterior deste diagnóstico.** Eu havia afirmado que a conta subia criativo com frequência excessiva, com base nos e-mails "Seus anúncios foram aprovados". Ao abrir o conteúdo desses e-mails, a maioria é de **outras contas de anúncio** que chegam na mesma caixa (Instituto O Setor Elétrico, CIDE, GTP Telles). A afirmação não se sustenta e foi retirada. Detalhes em [`07-fontes-e-proveniencia.md`](07-fontes-e-proveniencia.md).

O problema real não é rotação de criativo — é aritmética de ticket contra orçamento.

**A matemática crua a R$30/dia:**

```
R$30/dia × 30 = R$900/mês
CPM Brasil (moda/streetwear) ~R$30  →  ~30.000 impressões/mês
CTR 1,5%                            →  ~450 cliques  (CPC ~R$2,00)
CVR de loja de moda 1,5%            →  ~6,7 vendas/mês
```

Com o ticket médio atual (peça avulsa, R$150–170), isso dá **~R$1.050 de receita sobre R$900 de mídia = ROAS 1,17**. Descontado o custo do produto, **é prejuízo**.

**O ROAS de breakeven da BVBA é ~1,75** (margem bruta estimada de 57%). Qualquer coisa abaixo disso queima caixa. E o Meta precisa de **~50 conversões/semana por conjunto** para sair do aprendizado — a R$30/dia a BVBA entrega ~1,7/semana. **A conta nunca sai do aprendizado.**

> **Conclusão do diagnóstico:** o problema da BVBA não é a campanha. É que o ticket médio é baixo demais para o orçamento de mídia disponível. Otimizar segmentação ou criativo sem consertar isso é rearrumar cadeiras.

---

## 2. A estratégia central — três decisões que definem o plano

### Decisão 1 — O estoque encalhado NÃO recebe orçamento de mídia. Ele vira a alavanca do ticket.

Peça encalhada é peça que o mercado **já disse "não" ao preço cheio**. Pagar mídia para vendê-la é comprar a mesma audiência duas vezes, com um produto que já falhou uma vez. É o erro mais caro que uma marca pequena comete em liquidação.

Em vez disso, o arquivo vira **bônus** que destrava carrinho da coleção nova:

> **Acima de R$249, escolha 1 peça do arquivo — de graça.**

Três efeitos simultâneos, todos gratuitos:
1. **O ticket médio sobe** de ~R$160 para ~R$260 (o cliente sobe um degrau para destravar o bônus).
2. **O arquivo é liquidado** a custo de mídia **zero**.
3. **A percepção é de presente, não de queima** — o valor de marca do AW26 fica protegido. Loja que dá 40% off na home ensina o cliente a nunca mais pagar preço cheio.

Isso é um **Buy X Get Y Free** clássico (Attraction Offer), e é o coração do plano.

### Decisão 2 — A regra do ticket: 10% ou 20% de desconto é desperdício puro

Desconto moderado não muda comportamento de compra — só corta margem de quem já ia comprar. **Ou o item é bônus (100% off como add-on), ou é 50%+ dentro de um evento fechado.** Nada entre os dois. O arquivo antigo (2021–2023) entra no Archive Vault a 50–70% off, mas **apenas para a lista fechada, nunca na vitrine pública**.

### Decisão 3 — Mídia paga é o ÚLTIMO canal a ser ligado, não o primeiro

A ordem correta de aquisição para a BVBA, do mais barato ao mais caro:

| # | Canal | Custo | Quando |
|---|---|---|---|
| 1 | **Warm Outreach** — os 500+ telefones da base | **R$0** | Semana 1–2 |
| 2 | **Conteúdo orgânico** — IG 6.290 seguidores | **R$0** | Semana 2–3 |
| 3 | **Paid Ads** — R$30/dia no Meta | R$900/mês | Semana 4+ |

Mídia paga **amplifica** demanda — não a cria. Ligar R$30/dia antes de validar a oferta com a base morna é queimar o único orçamento disponível para descobrir algo que a base responderia de graça em 48h.

Há um benefício técnico decisivo nessa ordem: as vendas das semanas 1–3 **alimentam o Pixel com eventos de compra reais**. Quando o paid liga na semana 4, o algoritmo já tem sinal de quem é o comprador da BVBA — em vez de gastar as duas primeiras semanas (e ~R$400) descobrindo isso do zero.

---

## 3. Arquitetura de campanha — o que roda em cada canal

```
┌─────────────────────────────────────────────────────────────────┐
│  SEMANA 1-2 · CUSTO R$0 · Caixa rápido + aquecimento do Pixel   │
│                                                                 │
│  WhatsApp (base 500+)  ──►  ARCHIVE VAULT (48h, fechado)        │
│  Instagram Stories     ──►  50-70% off arquivo 2021-2023        │
│                             Meta: 15-25 vendas · R$2-4k         │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Pixel aquecido com compras reais
┌─────────────────────────────────────────────────────────────────┐
│  SEMANA 3 · CUSTO R$0 · Lançamento AW26 no orgânico             │
│                                                                 │
│  Reels da calça conversível (peça-herói)                        │
│  Teaser 72h ──► Drop ──► Lista VIP compra primeiro              │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Oferta validada, criativo testado
┌─────────────────────────────────────────────────────────────────┐
│  SEMANA 4+ · R$30/dia · Meta Ads                                │
│                                                                 │
│  1 campanha · 1 conjunto · 5 criativos · Advantage+ Audience    │
│  Objetivo: Vendas · Otimização: Compra · CBO R$30/dia           │
│  Oferta no anúncio: "Acima de R$249, arquivo grátis"            │
└─────────────────────────────────────────────────────────────────┘
```

### Por que 1 campanha e 1 conjunto — e não uma estrutura de funil

A tentação com R$30/dia é dividir: R$15 prospecção, R$10 retargeting, R$5 teste. **Isso é o pior movimento possível.** R$10/dia num conjunto de retargeting gera ~0,5 conversão/semana — o algoritmo nunca aprende, e você paga CPM de leilão sem nunca sair da fase de aprendizado em nenhum dos três.

Com orçamento restrito, a regra é: **menos campanhas, mais dados por campanha.** Todo o R$30 vai para um único conjunto amplo com Advantage+ Audience. O Meta já prioriza naturalmente quem engajou com a marca dentro de um público amplo — o retargeting acontece sozinho, sem custar um conjunto separado.

**O retargeting da BVBA é feito de graça**, por Stories, WhatsApp e e-mail. Não por mídia.

**Quando abrir um 2º conjunto:** só quando a loja passar de ~1.500 visitantes/mês. Aí sim divide R$21 prospecção / R$9 retargeting.

### Por que NÃO usar Advantage+ Shopping (ASC) agora

ASC pede **~50 compras/semana** de sinal consistente para funcionar. A BVBA está em ~2/semana. Rodar ASC nesse volume entrega pior que uma campanha de Vendas padrão. Reavaliar quando passar de 30 compras/semana.

### Por que 100% Meta e nada de Google Ads agora

Google Ads compra **intenção** — funciona quando existe gente buscando. O Perfil da Empresa no Google da BVBA registrou **54 visualizações em julho, 32 em junho, 35 em maio**. Não existe volume de busca de marca para capturar; dividir R$30/dia entre duas plataformas deixaria as duas abaixo do mínimo operacional.

**O que fazer no Google em vez disso, de graça:** ativar as **listagens gratuitas do Google Shopping** via integração da Nuvemshop com o Merchant Center. Custo R$0, alcance incremental. Google Ads pago entra na conversa quando o orgânico gerar busca de marca — provavelmente 3–4 meses após o AW26 pegar tração.

---

## 4. Metas e KPIs

### Matemática-alvo do plano

| Métrica | Hoje (estimado) | Meta em 90 dias |
|---|---|---|
| Ticket médio (AOV) | ~R$160 | **R$260** |
| Margem bruta | ~57% | 57% |
| Lucro bruto por pedido | ~R$91 | **~R$148** |
| **CAC máximo admissível** | R$91 | **R$148** |
| ROAS de breakeven | 1,75 | 1,75 |
| **ROAS-alvo (saudável)** | — | **2,5–3,0** |
| Vendas/mês por mídia paga | ~6 | **10–14** |
| CAC real projetado | ~R$135 | **R$64–90** |

A regra que governa tudo: **CAC < Lucro Bruto dos primeiros 30 dias.** Não receita — lucro bruto. É por isso que subir o AOV de R$160 para R$260 é o movimento mais importante do plano: ele **eleva o teto de CAC em 63%**, transformando um CAC de R$135 (hoje inviável) em um CAC confortável.

### Painel semanal (5 números, toda segunda-feira)

1. **Receita total** (paid + orgânico + WhatsApp) — separados
2. **AOV** — o número mais importante do plano; se não subir, nada mais funciona
3. **ROAS do Meta** — alvo ≥ 2,5
4. **Peças de arquivo liquidadas** — alvo: 114 → 0 em 90 dias
5. **CPA (custo por compra)** — alvo ≤ R$148, ideal ≤ R$90

### Critérios de decisão (definidos ANTES de gastar, para não decidir no calor)

| Situação | Ação |
|---|---|
| ROAS < 1,75 após 14 dias e R$420 gastos | Pausar paid. Problema é oferta ou página, não mídia. Voltar para orgânico |
| ROAS 1,75–2,5 | Manter. Trabalhar AOV e criativo, não mexer no orçamento |
| ROAS > 3,0 por 7 dias seguidos | Escalar +20% a cada 3–4 dias. Monitorar CPA por 48h a cada aumento |
| CPA sobe >25% após um aumento | Reverter para o valor anterior e esperar 72h |
| Criativo com frequência > 2,5 e CTR caindo | Fadiga. Trocar o hook, manter o conceito |

---

## 5. O que já está pronto para executar

Todo o material operacional está nos anexos — copy de anúncio, roteiros de Reels, scripts de WhatsApp e cronograma dia a dia estão prontos para copiar e colar.

**O que depende exclusivamente de acesso humano** (não pode ser feito autonomamente daqui):

- [ ] Recontar o estoque de arquivo (base para o volume de bônus)
- [ ] Confirmar os preços do AW26 (o plano usa estimativas — ver `01-ofertas.md`)
- [ ] Ligar a CAPI da Nuvemshop e validar o EMQ ≥ 7 — **bloqueante**
- [ ] Subir a campanha no Gerenciador de Anúncios
- [ ] Publicar no Instagram e disparar o WhatsApp
- [ ] Finalizar a edição do shooting de 25/07

**Próximo passo imediato:** ler [`06-medicao-e-checklist.md`](06-medicao-e-checklist.md) e executar o checklist bloqueante. Nada de mídia paga antes de o EMQ passar de 7 — com R$30/dia, sinal ruim significa orçamento inteiro desperdiçado.
