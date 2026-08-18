# BVBA Supply® — contexto de trabalho

Repositório da **BVBA Supply®**, marca brasileira de streetwear. Reúne o **agente de drop
da Nuvemshop** (código Python, em `agente_drop/`), o **planejamento de marketing**
(documentação operacional), o **diagnóstico e plano de mídia paga** (`midia-paga/`), a
**auditoria das imagens de e-commerce** e uma **pesquisa de mercado** independente.
O índice de tudo está no [`README.md`](README.md).

> ## 📍 O plano atual é [`PLANO.md`](PLANO.md) + [`midia-paga/`](midia-paga/)
>
> **⚠️ 18/08/2026 — a mídia paga foi religada por decisão do Victor**, com teto de R$30/dia.
> O plano de execução está em [`midia-paga/`](midia-paga/), construído sobre dados lidos
> direto da API da Meta. O `PLANO.md` (crescimento sem mídia, ativando os ~700 contatos
> mornos) **segue válido e continua sendo o motor principal** — a mídia amplifica, não
> substitui. As 40 conversas 1-a-1 por semana continuam sendo a métrica operacional nº 1.
>
> Os documentos em [`plano-360/`](plano-360/) são material de apoio. A copy, os scripts de
> WhatsApp e o checklist de medição seguem válidos; **a arquitetura de mídia paga de lá
> continua obsoleta** — a vigente é a de [`midia-paga/`](midia-paga/).

---

## ⚙️ Acordo de trabalho: rodar local por padrão

**Rode o Claude Code na máquina do Victor (macOS), não em sessão remota na nuvem.**

Motivo concreto, já verificado: o ambiente remoto tem política de egresso "negar tudo". O gateway responde `403 Forbidden` no CONNECT para `api.nuvemshop.com.br`, `graph.facebook.com`, `drive.google.com` e até `example.com`. Sessão remota **não alcança** o painel da Nuvemshop nem o Gerenciador de Anúncios da Meta, e nenhuma permissão de conta contorna isso — o bloqueio é anterior à credencial.

| | Sessão local (Mac) | Sessão remota (nuvem) |
|---|---|---|
| Meta Ads (Gerenciador) | ✅ | ✅ **via MCP** — autentica no servidor, contorna o egresso |
| Nuvemshop | ✅ | ❌ egresso 403 |
| Site bvbasupply.com.br | ✅ | ❌ egresso 403 |
| Obsidian (cofre local) | ✅ | ❌ não existe no container |
| Drive, Gmail, Calendar | ✅ | ✅ (via MCP, autentica no servidor) |
| GitHub | ✅ | ✅ |

Como iniciar na máquina:

```bash
git clone https://github.com/vicdeleao1997-arch/bvba-qa.git
cd bvba-qa
git checkout claude/trazer-projetos-pc-0vlyki
claude
```

Essa branch é a consolidada: traz os quatro projetos de uma vez. As branches
originais de cada um continuam existindo, intactas.

Se uma sessão remota for inevitável, ela ainda serve para Drive, Gmail, Calendar, GitHub e redação — mas **deve dizer explicitamente** o que não conseguiu verificar, em vez de assumir.

---

## Fatos verificados da marca

Confirmados em fonte oficial (Drive da marca, recibos da Meta, artifacts de planejamento).

- **Loja:** bvbasupply.com.br, plataforma **Nuvemshop**. CNPJ 41.242.625/0001-47
- **Instagram:** [@bvbasupply](https://www.instagram.com/bvbasupply/) · **Tagline:** *Supplying good trips!*
- **Conta de anúncios:** `CA - BVBA SUPPLY (321768910427826)` · gasto ~**R$1.100/mês** · teto de **R$30/dia**
- **Grupo VIP no WhatsApp:** **218 pessoas** — o canal mais valioso da marca
- **Base de clientes:** 500+ telefones em `Fonte clientes BVBA 04.2024.csv` (Drive), parada desde abr/2024

### Preços reais

| Carrinho | Cheio | Com VIP20 |
|---|---|---|
| 1 peça | R$129,90 | R$103,92 |
| 2 peças | R$219 | R$175,20 |
| 3 peças | R$299 | R$239,20 |

Camiseta e boné custam o mesmo (R$129,90). **Ticket atual: R$132.**

### Os números que governam as decisões

**Medidos na API da Meta em 18/08/2026** — substituem as inferências anteriores.

| | Registrado antes | **Medido** |
|---|---|---|
| Pedidos/mês | 2–3 (inferência) | **~7–8** (eventos de compra no pixel, 28 dias) |
| ROAS | ~0,4 (estimativa) | **0,12** (90 dias, atribuição mista) |
| CPM | — | **R$19,33** — 3× abaixo da referência de e-commerce |
| CTR | — | **2,75%** — 60% acima da referência |
| Custo por carrinho (melhor conjunto) | — | **R$3,85** |

**A leitura muda de lugar.** A conta compra atenção mais barata que o mercado e converte
visita em carrinho numa taxa saudável (9,9%). O que quebra é a medição: o evento `Purchase`
**não envia `content_ids` em nenhum dos 28 dias medidos**, e o `InitiateCheckout` dispara 5
vezes contra 8 compras. A Meta não consegue atribuir o que a loja vende.

Diagnóstico completo em [`midia-paga/01-diagnostico.md`](midia-paga/01-diagnostico.md).

**A alavanca de decisão:** com ticket de R$132, R$30/dia exigem 12,4 pedidos/mês só para
empatar no lucro bruto. Com o combo de 2 peças a R$219, exigem 7,5. Mover o ticket corta a
meta pela metade e é grátis.

### Coleções

- **Luzes do Irreal — Etapa Dois** (no ar em ago/2026): Museu · Sussurro Invisível · Espiral Surreal · Reflexo Errante · Frestas do Devaneio · Supplying Good Surrealism
- **AW 2026 "Drop 2"** (fichas técnicas fechadas, posterior): 8 camisetas oversized boxy, moletom canguru marrom café, e a `CJW-002` — calça oversized wide que **vira jorts por zíper divisório**, a peça de maior potencial criativo
- Cartela AW26, das fichas técnicas: off-white `#f2efeb` · bege `#c1a37f` · cinza claro `#e0e0e0`

---

## ⚠️ Regras da marca — não violar

1. **Política de IA em imagem:** *"peça real, nunca regenerada; só o ambiente é gerado por IA."* Nunca gere uma imagem que finja ser a peça — a cliente receberia algo diferente do anunciado. Cenário e fundo, sim; produto, não.
2. **Desconto:** ou o item é bônus (100% off como add-on), ou é 50%+ em evento fechado. Desconto de 10–20% na vitrine pública só corta margem de quem já ia comprar e destrói o preço de referência.
3. **Dados de cliente nunca entram no Git.** A base de telefones e qualquer export de pedidos ficam só no Drive — este repositório é publicado no GitHub. O `.gitignore` bloqueia os padrões, mas confira antes de commitar.
4. **Não fragmentar mídia.** Com R$30/dia, uma campanha e um conjunto. Dividir em três impede que qualquer um saia do aprendizado.

---

## Como ler o plano

Comece por [`plano-360/08-contexto-consolidado.md`](plano-360/08-contexto-consolidado.md) — tem precedência sobre os demais onde houver conflito, porque traz operação real em vez de estimativa. Depois [`07-fontes-e-proveniencia.md`](plano-360/07-fontes-e-proveniencia.md), que marca cada número como oficial, de terceiro ou estimativa.

O `README.md` da pasta traz o índice completo dos oito documentos.

---

## Próximos passos em aberto

1. **Exportar os pedidos da Nuvemshop** (últimos 12 meses, CSV). Resolve de uma vez AOV, ticket, mix e recompra — hoje inferidos. É o item de maior impacto.
2. ~~**Exportar o relatório da Meta**~~ ✅ **feito em 18/08/2026** via MCP — ver [`midia-paga/01-diagnostico.md`](midia-paga/01-diagnostico.md).
3. **Ler o resultado da janela VIP de 10–13/08**, que acabou de rodar.
4. ~~**Decidir sobre a mídia paga**~~ ✅ **decidido em 18/08/2026: religar com teto de R$30/dia.** Plano em [`midia-paga/`](midia-paga/). Repor estoque de brinde continua sendo pré-requisito — é ele que sustenta o ticket de R$219 que faz o orçamento caber.
5. **Validar CAPI e EMQ ≥ 7** na Nuvemshop — bloqueante para qualquer mídia. ⚠️ **Medido: CAPI ativa ✅, EMQ 6,1 ❌.** Faltam `em`, `ph` e `fbc`. Correção em [`midia-paga/02-correcoes-de-sinal.md`](midia-paga/02-correcoes-de-sinal.md).
6. **Auditar as imagens do acervo Magnific** contra a regra nº 1 acima.

## Onde as coisas estão no Drive

- `BVBA SUPPLY / 2026 / Coleções / Parte 2 / SHOOTING_25/07_V2/EDITADO` — 122 fotos editadas do shooting
- `.../EDITADO/FUNDO BRANCO — FINAL (97 fotos)` — shooting on-model em ciclorama cinza (o nome engana: não é packshot recortado)
- `.../FUNDO BRANCO — FINAL v2 (97 fotos · Magnific)` — **vazia**, só um stub de 160 bytes. O upload abortou
- `BVBA SUPPLY / 2026 / Outros Assets / BVBA_MAGNIFIC_HISTORICO` — imagens com prompt no nome do arquivo; auditar contra a regra de IA
- `BVBA SUPPLY / 2026 / Pedido Adriano — Fichas Técnicas 02.06.26.pdf` — specs do AW26
- `BVBA SUPPLY / Arquivos` — logo, contratos, base de clientes
