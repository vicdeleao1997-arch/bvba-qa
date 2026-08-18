# 02 — As cinco correções que precedem qualquer real de mídia

**Sem estas correções, R$30/dia compram exatamente o que compraram nos últimos 90 dias:
atenção barata e nenhuma venda medida.** Não é cautela — é a leitura direta do diagnóstico.

Tempo total: **4 a 6 horas de trabalho**, quase todo no painel da Nuvemshop e no Gerenciador
de Eventos. Nenhuma exige desenvolvedor externo.

---

## Ordem de execução

| # | Correção | Onde | Tempo | Impacto |
|---|---|---|---|---|
| 1 | `content_ids` + `value` no evento Purchase | Nuvemshop → Meta | 1–2h | 🔴 **Bloqueante** |
| 2 | Consertar InitiateCheckout | Nuvemshop | 1h | 🔴 **Bloqueante** |
| 3 | Enviar `em`, `ph`, `fbc` (EMQ 6,1 → 8+) | CAPI | 1–2h | 🔴 **Bloqueante** |
| 4 | Aposentar o pixel órfão | Gerenciador de Eventos | 5 min | 🟠 Alto |
| 5 | Padronizar atribuição | Gerenciador de Anúncios | 10 min | 🟠 Alto |

---

## 1. 🔴 O evento Purchase precisa enviar `content_ids`

**Sintoma medido:** 28 dias, `total_content_ids_count = 0` no Purchase. Todos os dias.
A Meta marca como `must_fix`.

### O que o evento deve carregar

```js
fbq('track', 'Purchase', {
  content_ids:  ['BVBA-CMS-004-M', 'BVBA-MLT-001-G'],  // SKU, igual ao do catálogo
  content_type: 'product',                              // ou 'product_group'
  value:        219.00,                                 // valor do pedido, número
  currency:     'BRL',
  num_items:    2,
  contents:     [                                       // recomendado
    { id: 'BVBA-CMS-004-M', quantity: 1, item_price: 129.90 },
    { id: 'BVBA-MLT-001-G', quantity: 1, item_price: 89.10  }
  ]
}, { eventID: pedido_id });                             // ← deduplicação web↔CAPI
```

### O ponto que decide

O `content_ids` precisa bater **exatamente** com o `retailer_id` do catálogo
`4171607529829243`. O `catalogo/produtos.csv` do repositório usa o padrão
`BVBA-CMS-004-M`. Confirme no Commerce Manager que o catálogo usa o mesmo — se a Nuvemshop
publicar o ID interno do produto em vez do SKU, o evento continua sem casar.

**Como validar:** o ViewContent já casa a **97,89%**. Ou seja, o mapeamento correto já existe
na loja — só não está sendo aplicado no Purchase. Copie o que o ViewContent faz.

### Verificação
Gerenciador de Eventos → Testar Eventos → uma compra real de ponta a ponta.
Depois, 24h após, confirme `matched_content_ids_count > 0` no Purchase.

---

## 2. 🔴 InitiateCheckout dispara em ~1 de cada 8 checkouts

**Sintoma medido:** 5 InitiateCheckout contra 8 Purchase em 28 dias. Aritmeticamente impossível.

**Causa provável:** o evento está preso a um botão específico ou a uma URL que a maioria dos
checkouts não passa (checkout transparente, compra pelo carrinho lateral, retorno de PIX).

**Correção:** disparar na entrada do checkout, por carregamento de página, não por clique de
botão. Mesma carga do Purchase (`content_ids`, `value`, `currency`, `eventID`).

**Meta de validação:** `InitiateCheckout ≥ 0,5 × AddToCart` e **sempre `≥ Purchase`**.
Hoje: 5 vs 55 ATC (9%) e 5 vs 8 compras (impossível).

> Enquanto não estiver consertado, **nenhuma campanha otimiza para InitiateCheckout.**
> Foi assim que R$591 evaporaram.

---

## 3. 🔴 EMQ 6,1 → 8+ : enviar e-mail, telefone e `fbc`

**Presentes hoje:** `ip_address` (100%), `user_agent` (100%), `fbp` (100%), `external_id` (33–100%)
**Ausentes:** `em`, `ph`, `fn`, `ln`, `ct`, `st`, `zp`, **`fbc`**

O checkout da Nuvemshop já coleta e-mail e telefone em toda compra. Falta repassá-los.

### Prioridade por ganho de EMQ

| Chave | Ganho | Origem |
|---|---|---|
| `em` (e-mail, SHA-256) | ⭐⭐⭐ maior sinal isolado | checkout |
| `ph` (telefone, SHA-256, E.164) | ⭐⭐⭐ | checkout |
| **`fbc`** (identificador do clique) | ⭐⭐⭐ **amarra clique → conversão** | cookie `_fbc` |
| `fn` / `ln` | ⭐⭐ | checkout |
| `ct` / `st` / `zp` | ⭐ | endereço de entrega |

**Regras de normalização** (errar aqui zera o ganho):
- minúsculas, sem espaços nas pontas, **antes** do SHA-256
- telefone em E.164 **sem** o `+` → `5511999999999`
- o `HANDOFF.md` item 2 já descreve a normalização da base de telefones; vale a mesma regra aqui

**`fbc` é o mais negligenciado e o mais valioso aqui.** Sem ele a Meta não liga o clique à
compra — é metade da explicação do ROAS 0,12. Capture o cookie `_fbc` (ou o parâmetro
`fbclid` da URL de entrada) e persista até o checkout.

**Meta:** EMQ ≥ 8,0 no Purchase. Isso satisfaz a condição nº 2 do gatilho do `PLANO.md`
(*"EMQ ≥ 7 com CAPI ativa e deduplicada"*).

---

## 4. 🟠 Aposentar o pixel órfão

`1629444861671282` ("BVBA Supply"), criado 08/05/2026, **nunca disparou**.

Existem dois datasets ativos no mesmo Business. Qualquer campanha nova apontada para o
errado nasce cega. Remova-o do Business ou renomeie para
`[NÃO USAR] BVBA duplicado — sem eventos`.

**O único pixel válido é `1076524503665763`.**

---

## 5. 🟠 Padronizar a janela de atribuição

Metade dos conjuntos mede `incrementality`, metade `1d_view_7d_click`. As duas leituras não
se comparam, e é por isso que o ROAS de conta não significa nada hoje.

**Padrão a adotar: `7d_click_1d_view` em tudo.**

Motivo: com ~8 compras/mês, `incrementality` não tem massa estatística para produzir leitura
confiável — ela precisa de volume para separar incremental de orgânico. Numa loja neste
tamanho ela devolve zero e parece fracasso quando não é.

Revisite `incrementality` quando a loja passar de 30 pedidos/mês.

---

## Checklist de liberação — mídia só sobe com os 5 verdes

```
[ ] 1. Purchase envia content_ids · matched_content_ids_count > 0 por 3 dias seguidos
[ ] 2. InitiateCheckout ≥ AddToCart × 0,5  E  ≥ Purchase
[ ] 3. EMQ do Purchase ≥ 8,0 · em + ph + fbc presentes
[ ] 4. Pixel 1629444861671282 aposentado
[ ] 5. Atribuição = 7d_click_1d_view em toda a conta
```

**Prazo realista: 5 a 7 dias**, contando as 48–72h que a Meta leva para recalcular o EMQ.

---

## Enquanto os cinco não fecham

O orçamento não fica parado — vai para a **Fase 0** do plano de mídia
([`03-plano-de-midia.md`](03-plano-de-midia.md)): recrutamento para o grupo VIP no WhatsApp,
que **não depende de nenhum desses eventos** para funcionar e já é o clique mais barato da
conta (R$0,40).

É a única frente de mídia que rende com o pixel quebrado — porque a conversão acontece no
WhatsApp, não no site.
