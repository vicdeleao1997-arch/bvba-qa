# 04 — Especificação de construção

Parâmetros exatos para montar no Gerenciador de Anúncios. Nada aqui é genérico: cada escolha
vem de um número medido na conta, citado ao lado.

**Identificadores:**
- Conta: `321768910427826`
- Pixel: **`1076524503665763`** (nunca `1629444861671282` — órfão)
- Catálogo: `4171607529829243`
- Business: `365891314722451`

---

## FASE 0 · Campanha de recrutamento VIP

Sobe **hoje**, roda enquanto as correções de sinal acontecem.

### Campanha
```
Nome:        [VIP] Recrutamento WhatsApp · R$30d · v20260818
Objetivo:    Tráfego  (OUTCOME_TRAFFIC)
Orçamento:   Conjunto (ABO)
Categoria especial: nenhuma
```

### Conjunto
```
Nome:               [VIP-CJ1] SE+Sul · 18-34 · Link grupo · R$30/d
Orçamento diário:   R$30,00
Otimização:         Cliques no link          ← NÃO "visualizações da landing page":
                                                o destino é o WhatsApp, não o site
Estratégia de lance: Maior volume
Atribuição:         7 dias clique, 1 dia visualização
Destino:            link de convite do grupo VIP no WhatsApp

Localização:  São Paulo · Rio de Janeiro · Minas Gerais · Paraná ·
              Espírito Santo · Santa Catarina · Rio Grande do Sul
Idade:        18–34                        ← CJ14/CJ10 (18-34) deram CTR 4,12–6,24%;
                                              os conjuntos 18-65 deram 1,73–2,21%
Gênero:       todos
Idioma:       português (BR)

Públicos personalizados (os que o CJ18 usou — R$0,40/clique):
  Seguidores IG BVBA
  ENGAJ. IG BVBA [365D]
  ENGAJ. IG BVBA [90D]
  Visitantes Site BVBA [180D]
  ViewContent Site BVBA [180D]
  AddToCart BVBA [180D]
  Viram catálogo BVBA [90D]
  Seguidores FB BVBA
  Engaj. FB BVBA 365D

EXCLUIR (obrigatório — não pagar por quem já está dentro):
  Grupo VIP — Membros (SE+Sul)
  [VIP] WhatsApp BVBA · grupo · 218 membros · 2026-06-29

Advantage+ Audience:   LIGADO
Posicionamentos:       Advantage+ (automáticos) — inclui Threads, CPM mais baixo
```

### Anúncios — 3, formatos distintos
```
[VIP-AD1]  vídeo   Teaser do gato no MASP  (já produzido — CPM histórico R$6,56–8,12)
[VIP-AD2]  vídeo   Corte de 8s da CJW-002: a calça virando jorts pelo zíper
[VIP-AD3]  estático  Card "o drop abre primeiro no grupo"
```

> **Por que vídeo primeiro:** `[CJ18-AD10]` entregou CPM **R$6,56** e `[CJ18-AD5]` **R$8,12**,
> contra R$17–45 dos estáticos de catálogo. Vídeo compra atenção por 1/3 a 1/7 do preço.

---

## FASE 1 · Campanha de vendas

**Só sobe com os 5 itens do checklist de liberação verdes.** Ao subir, **pausar a Fase 0** —
uma campanha por vez (regra nº 4 do `CLAUDE.md`).

### Campanha
```
Nome:        [VENDAS] Etapa Dois · Combo 2 peças · R$30d · v20260825
Objetivo:    Vendas  (OUTCOME_SALES)
Orçamento:   Conjunto (ABO)
Catálogo:    4171607529829243  (conectado)
```

### Conjunto — **um só**
```
Nome:                [V-CJ1] LAL1% + Adv+ · BR · ATC · R$30/d
Orçamento diário:    R$30,00
Evento de conversão: AddToCart        ← ~55/mês no site. Purchase (8) e
                                        InitiateCheckout (5) não têm massa
Local da conversão:  Site
Pixel:               1076524503665763
Estratégia de lance: Maior volume (sem teto de custo no início)
Atribuição:          7 dias clique, 1 dia visualização

Localização:  Brasil                   ← CJ6 (BR amplo) deu R$3,85/ATC e CPM R$17,09.
                                          CJ14 (Sudeste restrito) deu R$7,63/ATC e CPM R$45,38.
                                          Restringir geo encareceu 2,6× o carrinho.
Idade:        18–34
Gênero:       todos

Públicos (só os dois que produziram — não empilhar):
  Semelhante (BR, 1%) - Compraram site BVBA [180D]
  Semelhante (BR, 1%) - clientes compradores bvba.csv

EXCLUIR:
  Compraram site BVBA [180D]
  [BVBA] Purchase - 730D

Advantage+ Audience:   LIGADO        ← os 2 melhores conjuntos (R$3,80–3,85/ATC) tinham
                                        ligado; os piores (R$16–58/ATC) tinham desligado
Advantage+ Criativo:   LIGADO (texto, brilho, música)
Posicionamentos:       Advantage+ (automáticos)
```

> **O que NÃO fazer, com o número do porquê:**
> - ❌ empilhar 18 públicos como o CJ18 → vira massa indistinta, não se aprende nada
> - ❌ desligar o Advantage+ Audience → CJ2 (desligado) custou R$16,23/ATC contra R$3,85 do CJ6
> - ❌ otimizar InitiateCheckout → R$591 já foram por esse ralo
> - ❌ restringir para SP/RJ no começo → CPM sobe 2,6× sem ganho proporcional
> - ❌ abrir um segundo conjunto abaixo de R$60/dia

### Anúncios — 4, com diversidade real
Ver [`05-criativos.md`](05-criativos.md). Regra: **4 conceitos distintos**, nunca 4 variações
do mesmo. Andromeda agrupa criativos com similaridade >60% e faz um suprimir o outro.

---

## Higiene antes de subir qualquer coisa

```
[ ] Arquivar as 49 campanhas pausadas ou renomear com prefixo [ARQ]
    → hoje o Gerenciador está ilegível e favorece reativar a coisa errada
[ ] Apagar/renomear o pixel órfão 1629444861671282
[ ] Confirmar que [FASE 2] e [FASE 3] (v20260814, R$0,00 gastos) seguem pausadas
    ou arquivá-las — foram criadas e nunca rodaram
[ ] Padronizar atribuição em 7d_click_1d_view na conta inteira
[ ] Conferir que o catálogo 4171607529829243 tem os 11 SKUs do AW26 com preço
    → catalogo/PENDENTE.md acusa 55 erros: as 11 peças estão sem preço e sem foto
```

> ⚠️ O último item é bloqueante para anúncio de catálogo. `python3 -m agente_drop validar`
> acusa hoje **55 erros e 11 avisos** — as peças do AW26 não têm preço nem foto. Um catálogo
> incompleto vira anúncio com placeholder cinza.

---

## Calendário das primeiras 5 semanas

| Semana | O que acontece | Orçamento |
|---|---|---|
| **1** (18–24/08) | Fase 0 no ar. Correções 1–5 em execução. Brinde muda para tamanho de carrinho | R$30/dia → VIP |
| **2** (25–31/08) | Checklist verde → sobe Fase 1, pausa Fase 0. **7 dias de silêncio** | R$30/dia → vendas |
| **3** (01–07/09) | Primeira leitura. Só troca criativo se custo/ATC > R$15 | R$30/dia |
| **4** (08–14/09) | Rotação de criativo. Frequência > 3,5 → trocar | R$30/dia |
| **5** (15–21/09) | Avaliar migração para Purchase (gatilho: ≥30 compras medidas/mês) | R$30/dia |

**Teto absoluto: R$900/mês.** Só sobe após 7 dias seguidos de ROAS ≥ 2,0, e em +20% a cada
4 dias — nunca dobrando.
