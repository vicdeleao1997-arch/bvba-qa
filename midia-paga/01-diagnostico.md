# 01 — Diagnóstico da conta e do funil

**18/08/2026** · Conta `CA - BVBA SUPPLY` (`321768910427826`) · Business `BVBA Supply` (`365891314722451`)
Dados lidos **direto da API da Meta** nesta sessão, não estimados.

---

## O veredito em uma frase

> **A mídia da BVBA não falha por criativo, por público ou por orçamento. Falha porque o
> evento de compra não envia `content_ids` — nenhum, nunca. A Meta vê o dinheiro entrar
> e não sabe de onde veio.**

Tudo o mais no diagnóstico decorre disso.

---

## 1. O que os números realmente dizem

### Conta, últimos 90 dias (20/05 → 18/08/2026)

| Métrica | Valor real | Referência e-commerce | Leitura |
|---|---|---|---|
| Gasto | R$2.253,32 | — | ~R$25/dia efetivos |
| Impressões | 116.576 | — | |
| **CPM** | **R$19,33** | ~R$65 (US$12,50) | 🟢 **3× mais barato** |
| **CTR** | **2,75%** | 1,71% | 🟢 **60% acima** |
| CPC | R$0,70 | — | 🟢 barato |
| Alcance | 52.196 | — | |
| Frequência | 2,23 | <3,0 | 🟢 saudável |
| **ROAS** | **0,12** | 2,19 mediana | 🔴 **1/18 da referência** |

**Isto não é uma conta mal operada na camada de mídia.** Compra atenção mais barata que o
mercado e com engajamento acima da média. O colapso é exclusivamente na conversão medida.

### O funil de 90 dias

```
116.576 impressões
   ↓  2,2% (link CTR)
 2.572 cliques no link
   ↓  70%            ← 30% de perda entre clique e carregamento da página
 1.799 visualizações da landing page
 1.851 ViewContent
   ↓  9,9%           ← 🟢 taxa SAUDÁVEL para moda
   183 AddToCart
   ↓  6,6%           ← 🔴 deveria ser 40–60%
    12 InitiateCheckout
   ↓  8,3%
     1 Compra          custo por compra: R$2.253,32
```

O site converte visita em carrinho **bem**. O que quebra é tudo depois do carrinho — e a
próxima seção mostra que a quebra é de **medição**, não de comportamento do cliente.

---

## 2. 🔴 A causa raiz: o evento de compra é cego

Diagnóstico do pixel `1076524503665763` ("BVBA Supply pixel OFICIAL") contra o catálogo
`4171607529829243`, 28 dias (21/07 → 17/08):

| Evento | Dispara? | Envia `content_ids`? | Taxa de correspondência |
|---|---|---|---|
| ViewContent | ✅ 586 | ✅ sim | **97,89%** 🟢 |
| AddToCart | ✅ 55 | ⚠️ **só em 3 dos 28 dias** | 100% quando envia |
| **Purchase** | ✅ ~8 | ❌ **ZERO, todos os 28 dias** | **0%** 🔴 |
| InitiateCheckout | ⚠️ 5 | ❌ | — |

A própria Meta classifica dois desses como **`must_fix`**:

> `missing_event` · **AddToCart** — *"Your pixel might not be sending events from your website."*
> `missing_event` · **Purchase** — *"Your pixel might not be sending events from your website."*

### Por que isso destrói tudo

1. **Atribuição morre.** Sem `content_ids`, a compra não se liga ao produto nem ao anúncio
   que a gerou. Daí ROAS 0,12 com 183 carrinhos.
2. **Catálogo/DPA fica inútil.** Todo anúncio de vendas da conta é anúncio de catálogo. Sem
   sinal de compra ligado ao produto, o catálogo não sabe o que promover nem para quem
   reimpactar.
3. **O otimizador não aprende.** A Meta otimiza para o que consegue medir. Não conseguindo
   medir compra, otimiza para o proxy mais próximo — e erra.

### O erro estrutural do InitiateCheckout

**O pixel registrou 8 compras e apenas 5 InitiateCheckout no mesmo período.**
É impossível comprar sem iniciar a finalização. O evento está quebrado — dispara em algo
como 1 de cada 8 checkouts reais.

**E R$591 foram gastos otimizando exatamente para ele:**

| Conjunto | Gasto | Otimização | InitiateCheckout obtidos |
|---|---|---|---|
| `[CJ9] PROSPEC · LAL · SP/RJ · IC` | R$224,16 | InitiateCheckout | **0** |
| `[CJ2] PROSPEC · GEO SP+RJ+MG+PR · IC` | R$129,86 | InitiateCheckout | 1 |
| `[CJ1] BRASIL · 18-35 · IC` | R$120,91 | InitiateCheckout | 1 |
| `cj3 \| semelhante \| Iniciar finalização` | R$115,61 | InitiateCheckout | 2 |

Um quarto de todo o orçamento de 90 dias foi para leilões mirando um evento que o site
quase não emite.

---

## 3. 🔴 EMQ 6,1 — e faltam as chaves que importam

| Evento | EMQ | Chaves presentes |
|---|---|---|
| PageView | 6,1 | ip · user_agent · fbp · external_id (40,9%) |
| ViewCategory | 6,1 | ip · user_agent · fbp · external_id (100%) |
| ViewContent | 6,1 | ip · user_agent · fbp · external_id (33,3%) |

**Purchase e AddToCart nem aparecem no relatório de qualidade** — não têm dado suficiente
para serem pontuados.

**Ausentes por completo:** `em` (e-mail), `ph` (telefone), `fn`/`ln` (nome), `ct`/`st`/`zp`
(cidade/estado/CEP) e **`fbc`** (identificador do clique).

O checkout da Nuvemshop **captura e-mail e telefone em toda compra**. Eles simplesmente não
são repassados. `em` + `ph` + `fbc` normalmente levam EMQ de ~6 para 8–9.

Sem `fbc`, a Meta não consegue amarrar o clique à conversão. É a segunda metade da explicação
do ROAS 0,12.

---

## 4. 🟠 Fragmentação — viola a regra nº 4 do `CLAUDE.md`

**12 conjuntos ativos em 90 dias para R$2.253 de gasto** — média de R$188 por conjunto.

Um conjunto precisa de ~50 conversões por semana para sair do aprendizado. O melhor conjunto
da conta acumulou **62 AddToCart em toda a sua vida**. Nenhum chegou perto. **Nenhum conjunto
desta conta jamais saiu da fase de aprendizado.**

Pior: os orçamentos diários somados dos conjuntos simultâneos (R$15 + R$30 + R$30 + R$30 +
R$11 + R$10…) **excedem em muito o teto de R$30/dia**. O teto existia no papel, por conjunto,
nunca na conta.

### Atribuição inconsistente — os números não são comparáveis entre si

| Configuração | Conjuntos |
|---|---|
| `incrementality` | CJ6, CJ9, CJ2, CJ1, cj3 |
| `1d_view_7d_click` | CJ14, CJ18, CJ10, CJ-A+A, c1, cj1-base, cj6-LAL |

Metade da conta mede incrementalidade (leitura conservadora, só conversão incremental), a
outra metade mede 7 dias de clique. **O ROAS de conta de 0,12 é a média de duas réguas
diferentes** — e por isso não é comparável nem com o "ROAS ~0,4" registrado no repositório,
nem com benchmark de mercado.

---

## 5. 🔴 Criativo: um só, replicado em 8 conjuntos

Todo anúncio de vendas da conta se chama **"Catálogo"**:

`[CJ6-AD1] Catálogo` · `[CJ9-AD1] Catálogo` · `[CJ14-AD1] Catálogo` · `[CJ2-AD1] Catálogo` ·
`[CJ10-AD1] Catálogo` · `[CJ11-AD1] Catálogo` · `[CJ12-AD1] Catálogo` · `[CJ13-AD1] Catálogo`

### Pontuação de diversidade criativa (rubrica Andromeda)

| Eixo | Nota | Por quê |
|---|---|---|
| Diversidade de conceito | 0/2 | Uma mensagem só: o catálogo |
| Diversidade de formato | 0/2 | Só catálogo estático nas campanhas de venda |
| Diversidade visual | 0/2 | Mesmo tratamento em todos |
| Diversidade de hook | 0/2 | Nenhum vídeo nas campanhas de venda |
| Diversidade de headline | 0/2 | — |
| **Total** | **0/10** | 🔴 **RISCO ALTO de agrupamento por Entity-ID** |

Desde o Andromeda (out/2025), criativos com Similarity Score >60% são agrupados e disputam o
**mesmo ticket de retrieval** — só um entrega por oportunidade. Oito cópias do mesmo anúncio
em oito conjuntos não multiplicam alcance: **competem entre si e suprimem umas às outras.**

### E o vídeo, que a marca já tem, é 4× mais barato

| Anúncio | Formato | CPM | Observação |
|---|---|---|---|
| `[CJ18-AD10]` A/B escada · ângulo EVENTO | vídeo | **R$6,56** | 146 vídeos a 75% |
| `[CJ18-AD5]` Teaser Museu + benefícios VIP | vídeo | **R$8,12** | 348 vídeos a 75%, 264 ThruPlay |
| `[CJ6-AD1]` Catálogo | estático | R$17,09 | |
| `[CJ14-AD1]` Catálogo | estático | R$45,38 | |

**O vídeo compra atenção por 1/3 a 1/7 do preço do catálogo estático.** A marca já tem o filme
de 25s do assalto ao museu e o teaser do gato no MASP, produzidos e parados.

---

## 6. 🟢 O que já funciona (e deve ser preservado)

### Os dois melhores conjuntos da conta

| Conjunto | Gasto | CTR | ATC | **Custo por ATC** |
|---|---|---|---|---|
| `[CJ6] PROSPEC · LAL · ATC · R$15/d` | R$238,60 | 4,48% | 62 | **R$3,85** |
| `[CJ9] PROSPEC · LAL · SP/RJ · IC` | R$224,16 | 4,97% | 59 | **R$3,80** |
| CJ14 (Sudeste, 18-34) | R$213,68 | 6,24% | 28 | R$7,63 |
| CJ2 | R$129,86 | 2,12% | 8 | R$16,23 |
| cj3 | R$115,61 | 2,21% | 2 | R$57,81 |

**Fórmula vencedora, empiricamente:** Semelhante 1% + **Advantage+ Audience LIGADO** + geo
amplo + otimização em AddToCart + exclusão de compradores. Os dois melhores conjuntos usam
exatamente isso. Os piores desligam o Advantage+ Audience e empilham público.

### A idade importa

Conjuntos em **18-34** entregaram CTR 4,12–6,24%. Conjuntos em **18-65** entregaram 1,73–2,21%.
A exceção (CJ6 a 4,48% em 18-65) tinha Advantage+ Audience ligado, que corrige a faixa sozinho.

### O canal mais barato da conta inteira

`[CJ18] Convite DIRETO grupo VIP` — R$173,27 · CPM **R$7,54** · 429 cliques · **~R$0,40 por
clique**. É o melhor custo de aquisição da conta, e alimenta o grupo de WhatsApp que o
`PLANO.md` identifica como o canal onde a venda de fato fecha.

---

## 7. As campanhas da abertura pública nunca rodaram

| Campanha | Início programado | Gasto |
|---|---|---|
| `[FASE 2] Drop Museu · Vendas · v20260814` | 14/08 20h00 | **R$0,00** |
| `[FASE 3] Etapa Dois · Retargeting abertura pública` | 14/08 20h00 | **R$0,00** |

Sem erro de veiculação registrado — foram criadas e deixadas pausadas.
**A abertura pública de 14/08 rodou com zero apoio de mídia.**

---

## 8. Pixel órfão

| Dataset | Criado | Último disparo |
|---|---|---|
| `1076524503665763` — BVBA Supply pixel OFICIAL | 22/01/2024 | 18/08/2026 ✅ (web **e servidor**) |
| `1629444861671282` — BVBA Supply | 08/05/2026 | **nunca** |

O segundo dataset nunca disparou. Existe desde maio e é uma armadilha: qualquer campanha
apontada para ele opera com sinal zero. **Deve ser aposentado.**

Nota positiva: o CAPI **está ativo** — `server_last_fired_time` = 18/08/2026 02:40. O
repositório tratava isso como incerto.

---

## 9. Nota de saúde da conta

```
Nota de Saúde Meta Ads: 35/100  (D)

Pixel / CAPI       40/100  ████░░░░░░  (peso 30%)
Criativo           20/100  ██░░░░░░░░  (peso 30%)
Estrutura          20/100  ██░░░░░░░░  (peso 20%)
Público            65/100  ███████░░░  (peso 20%)
```

O perfil é atípico e é uma boa notícia: **público é a dimensão mais forte e criativo/medição
as mais fracas.** Público é o que custa caro e demora a construir — a BVBA já tem 18 públicos
personalizados, semelhantes de 1% e 2% testados, e o Advantage+ Audience validado. Medição e
criativo se consertam em dias.

---

## 10. O volume real de pedidos — o repositório subestima

O `PLANO.md` e o `08-contexto-consolidado.md` trabalham com **"2 a 3 pedidos/mês"**, inferido de
uma frase do plano de 02/08.

**O pixel registra ~8 compras em 28 dias** (21/07 → 17/08) — janela que inclui o VIP de 10–13/08.

| | Repositório | Medido no pixel |
|---|---|---|
| Pedidos/mês | 2–3 (inferência) | **~7–8** |

Distribuição: 21/07, 23/07, 25/07 (período de campanha paga) e 10/08 ×2, 11/08 ×2 (janela VIP,
via WhatsApp). Aproximadamente **metade orgânica/WhatsApp, metade no período de mídia**.

**A meta de 15 pedidos/mês do `PLANO.md` está a 2× de distância, não a 6×.**

> ⚠️ Ressalva honesta: o pixel conta eventos de compra, não pedidos pagos na Nuvemshop.
> Pedido cancelado, boleto não pago e PIX abandonado contam aqui. O export da Nuvemshop
> continua sendo o item de maior valor da lista de pendências — mas a ordem de grandeza
> mudou, e para melhor.

---

## 11. O que não consegui verificar

Registro explícito, conforme o acordo do `CLAUDE.md`:

| Item | Por quê |
|---|---|
| **Front-end do site** (velocidade, checkout, frete, meios de pagamento, mobile) | Egresso bloqueado — `bvbasupply.com.br` retorna 403 no proxy. Diagnostiquei o **comportamento** do site pelo pixel, não a interface |
| Pedidos reais da Nuvemshop | Mesma razão. `api.nuvemshop.com.br` bloqueado |
| Taxa de deduplicação web↔servidor | A API não expõe. Contagens idênticas (ATC 55/55, IC 5/5) são consistentes com CAPI correto, mas não provam deduplicação |
| Verificação de domínio e AEM | Não expostos por esta API |

### 🟢 Correção ao acordo de trabalho do `CLAUDE.md`

O `CLAUDE.md` afirma que sessão remota **não alcança** a Meta. **Isso está desatualizado.**
O MCP do Meta Ads autentica no servidor e contorna o bloqueio de egresso — todo este
diagnóstico foi feito de sessão remota.

| | Sessão local | Sessão remota |
|---|---|---|
| Meta Ads | ✅ | ✅ **via MCP** (antes marcado ❌) |
| Nuvemshop, site | ✅ | ❌ egresso 403 |

Isso também resolve o item 2 do `HANDOFF.md` ("exportar o relatório da Meta") — feito aqui.

E encerra a dúvida do `07-fontes-e-proveniencia.md` sobre qual conta está ativa: as campanhas
`CJ6`, `CJ9`, `CJ14`, `CJ18` estão todas em **`321768910427826`**. O outro identificador não
é uma segunda conta em operação.
