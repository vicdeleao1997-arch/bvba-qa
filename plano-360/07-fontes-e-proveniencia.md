# 07 — Auditoria de fontes e procedência

Este documento classifica **cada dado** usado no plano pela sua origem, para separar o que é fato verificado na fonte oficial da BVBA do que é estimativa minha. Auditoria feita em 11/08/2026.

## Legenda de confiança

| Nível | Significado |
|---|---|
| 🟢 **OFICIAL** | Veio de uma fonte controlada pela BVBA: Drive da marca, recibos da Meta no e-mail operacional, fichas técnicas de produção |
| 🟡 **TERCEIRO** | Fonte externa não controlada pela marca (resultado de busca na web). Plausível, mas não confirmado na origem |
| 🔴 **ESTIMATIVA** | **Número meu**, não da BVBA. Referência de mercado ou suposição. Precisa ser substituído por dado real |

---

## 1. 🔴 CORREÇÃO IMPORTANTE — um erro do diagnóstico original

O `README.md` afirmava:

> *"Há um fluxo constante de e-mails 'Seus anúncios foram aprovados' — em 31/07 foram 4 aprovações no mesmo dia... Isso descreve uma conta que sobe criativo com muita frequência."*

**Isso estava errado.** Abri o conteúdo completo desses e-mails. A caixa `victor.meyagusko1@gmail.com` recebe notificações de **múltiplas contas de anúncio**, não só da BVBA:

| Conta | Natureza | Gasto observado |
|---|---|---|
| **CA - BVBA SUPPLY** (321768910427826) | A marca | R$350 a R$759 por recibo |
| Instituto O Setor Elétrico (509353363688317) | Cursos de engenharia elétrica | R$3.268 a R$3.941 |
| CIDE (938854617813301) | Terceiro | R$1.210 a R$1.707 |
| CA01 - GTP Telles (1424669272477) | Terceiro | R$0,01 a R$14,52 |

Das quatro aprovações de 31/07, **três eram do Instituto O Setor Elétrico** (cursos de SPDA, subestações, PSCAD) — nada a ver com a BVBA. A conclusão de "rotação excessiva de criativo na conta da BVBA" **não se sustenta** e foi removida do diagnóstico.

**O que continua válido:** os valores de gasto da BVBA, porque os recibos identificam a conta nominalmente. Esses estão certos.

**Lição operacional:** qualquer leitura futura dessa caixa precisa **filtrar pelo ID 321768910427826**. Agregar sem filtrar mistura o orçamento da BVBA com o de outros clientes.

---

## 2. 🟢 A campanha que está no ar AGORA (dado novo, não estava no plano)

O mesmo e-mail revelou os criativos reais da BVBA aprovados em 31/07 — quatro anúncios de uma campanha **ativa**:

| Ad | Ângulo | Conteúdo real do anúncio |
|---|---|---|
| `[CJ18-AD6]` | FASE 1 · A/B ângulo OFERTA | *"A Etapa Dois de Luzes do Irreal está chegando 🐈‍⬛ ... 20% OFF com cupom exclusivo · Os 3 primeiros pedidos levam 1 peça da coleção anterior à escolha · Acesso antecipado — dia 10.08"* |
| `[CJ18-AD7]` | FASE 1 · A/B ângulo EVENTO | *"A Ala Irreal abre segunda, 10.08, às 19h30 · Primeiro no grupo VIP. Só depois pro resto do mundo."* |
| `[CJ18-AD8]` | JANELA · AO VIVO | *"A ALA IRREAL ESTÁ ABERTA · O drop novo está rolando AGORA no grupo VIP — e só lá. 20% OFF · Aberto só até quinta, 13.08 · Sexta abre pro público, sem desconto"* |
| `[CJ19-AD1]` | FASE 3 · DPA retargeting | *"A Etapa Dois de Luzes do Irreal está no ar pra todo mundo — **2 peças por R$219 com frete grátis · 3 por R$299**. Enquanto tiver estoque."* |

### O que isso muda no plano

Quatro premissas minhas estavam desatualizadas:

1. **A coleção em lançamento não é o AW26** — é **"Luzes do Irreal — Etapa Dois"**, que abriu em **10/08 às 19h30** (ontem) e fecha para o VIP em **13/08**. O AW26 vem depois.
2. **A Lista VIP já existe.** Recomendei criar uma; ela está em operação e é o canal de acesso antecipado.
3. **A mecânica de arquivo-como-bônus já está em uso**: *"os 3 primeiros pedidos levam 1 peça da coleção anterior à escolha"*. A recomendação central do plano já foi intuída pela marca — o que o plano acrescenta é transformá-la de brinde para os 3 primeiros em **gatilho permanente de ticket** (acima de R$249).
4. **Já existe preço de bundle real**: **2 peças por R$219 · 3 por R$299**. Isso substitui minhas estimativas de preço — ver seção 4.

> ⚠️ Também apareceu uma inconsistência a esclarecer: os anúncios da BVBA foram aprovados na conta `act=23858892751030364`, mas os recibos de cobrança vêm de `321768910427826`. São identificadores diferentes. Pode ser duas contas de anúncio distintas ou uma conta de agência veiculando pela marca. **Confira no Gerenciador qual conta está de fato ativa** — o plano assume 321768910427826 porque é a que aparece nominalmente como "CA - BVBA SUPPLY" nos recibos.

---

## 3. 🟢 Dados de fonte oficial (pode confiar)

| Dado | Valor | Fonte exata |
|---|---|---|
| Coleção AW26 — 11 SKUs, modelagens, cores, aviamentos | — | `Fichas Técnicas 02.06.26.pdf` e `Fichas Técnicas reestock.pdf`, Drive da marca |
| Calça `CJW-002` conversível por zíper | — | Ficha técnica: *"Zíper divisório Jorts → Calça"* |
| Cartela do AW26 | Off-white `#f2efeb`, Bege `#c1a37f`, Cinza claro `#e0e0e0` | Especificado nas fichas `CMS-009/010/011` |
| Gasto da BVBA no Meta | R$759,33 (02/08) · R$350,41 (13/07) · R$759,32 (03/07) · R$385,52 (13/06) · R$759,27 (02/06) | Recibos da Meta, conta 321768910427826 |
| Estoque de arquivo | ~114 peças | Planilha `Controle Estoque`, Drive — **Coleção 01/2023** |
| Base de clientes | 500+ telefones | `Fonte clientes BVBA 04.2024.csv`, Drive |
| Shooting AW26 | 122 fotos editadas + 97 packshots | Drive, pasta `SHOOTING_25/07_V2` |
| Perfil da Empresa no Google | 54 (jul) · 32 (jun) · 35 (mai) visualizações | Relatórios do Google Business Profile por e-mail |
| Plataforma da loja | Nuvemshop | Confirmado por `Logo BVBA Nuvemshop DANFE.jpg` no Drive e pela relação comercial no e-mail |
| CNPJ | 41.242.625/0001-47 | Notificação extrajudicial no Drive |
| e-CNPJ A1 emitido | 08/07/2026 | E-mails da Certisign |

---

## 4. 🔴 Estimativas minhas — SUBSTITUIR por dado real

Estes números **não vieram da BVBA**. Eu os usei para tornar o modelo calculável, e estão marcados como estimativa no `01-ofertas.md`. Agora há dado melhor para parte deles.

| Dado | O que usei | Situação real |
|---|---|---|
| Preço camiseta AW26 | R$169 | **Substituir.** O anúncio real pratica **2 peças R$219 · 3 por R$299** (≈R$110 e R$100/peça). O ticket real é bem menor do que supus |
| Preço moletom / calça / boné | R$299 / R$349 / R$129 | Nunca confirmados. Conferir na loja |
| Custo de produção | R$68 a R$155 | **Estimativa pura.** Há um dado de 2022 no e-mail com a BC Company: camiseta com estampa de 5 cores a **R$49,90/peça** — base histórica real, mas de 4 anos atrás |
| Margem bruta | 57% | Derivada dos preços estimados. Recalcular |
| CPM Brasil | R$30 | Referência de mercado, não da conta |
| CTR | 1,5% | Referência de mercado |
| Taxa de conversão | 1,5% | Referência de mercado |
| AOV atual | ~R$160 | **Suposição.** Com bundle de 2/R$219 o AOV real pode já estar acima disso |
| Ticket-alvo | R$260 | Meta derivada das estimativas acima |

**Consequência:** a conclusão qualitativa do plano — *ticket baixo demais para o orçamento de mídia; subir AOV é a alavanca* — continua de pé, e o bundle 2/R$219 mostra que a marca já se move nessa direção. Mas **os números precisos de ROAS, CAC e breakeven precisam ser refeitos** com preço e custo reais. A aba "Calculadora Oferta & Margem" da planilha faz isso sozinha: troque as entradas e tudo recalcula.

---

## 5. 🟡 Dados de terceiros (não confirmados na origem)

| Dado | Valor | Por que é fraco |
|---|---|---|
| Seguidores no Instagram | 6.290 | Veio de trecho de busca na web, não da API do Instagram. **Confirme no app** |
| Frete grátis acima de R$199 | — | Trecho de busca. O anúncio real diz *"2 peças por R$219 **com frete grátis**"*, o que sugere regra por combo, não por valor |
| Pix com 5% de desconto | — | Trecho de busca, não confirmado |
| Tagline "Supplying good trips!" | — | Aparece na bio pública e é consistente com o material do Drive — provavelmente correto |

Motivo da fraqueza: **`bvbasupply.com.br` está bloqueado pelo proxy de rede desta sessão.** Não consegui ler a loja diretamente em nenhum momento; tudo sobre o site veio de trecho de busca.

---

## 6. ❌ O que NÃO foi possível verificar

| Lacuna | Por quê | Impacto |
|---|---|---|
| **Volume e valor de vendas** | Não existe nenhum e-mail de pedido da Nuvemshop nesta caixa. Busquei por "novo pedido", "nova venda", "pedido pago", "parabéns pela venda" — zero resultado. As notificações devem ir para `contato@bvbasupply.com.br` | **Maior lacuna do plano.** ROAS e AOV atuais são inferência, não medição |
| Métricas da campanha no Meta | Sem acesso ao Gerenciador; a Graph API está bloqueada pelo proxy | Não sei o ROAS real da campanha que está no ar |
| Estoque atual do arquivo | Última contagem estruturada é de **01/2023**; houve "Luzes do Irreal" (dez/2025) e uma SALE (jan/2026) depois | As 114 peças são um teto histórico, não o saldo de hoje |
| Estado da CAPI e do EMQ | Sem acesso ao painel da Nuvemshop nem ao Gerenciador de Eventos | O item bloqueante do checklist continua não verificado |
| Fotos publicadas na loja | Domínio bloqueado pelo proxy | Por isso a auditoria de imagem roda sobre a **fonte no Drive**, não sobre o site |

---

## 7. Como fechar as lacunas

Em ordem de impacto:

1. **Exportar os pedidos da Nuvemshop** (Admin → Pedidos → Exportar CSV, últimos 12 meses). Resolve de uma vez AOV real, ticket, mix de produto, taxa de recompra e sazonalidade — os números que hoje são estimativa.
2. **Exportar o relatório da campanha no Gerenciador** (últimos 90 dias, por campanha/conjunto/anúncio, com gasto, compras, valor de conversão, CTR, CPM, frequência). Dá o ROAS real.
3. **Recontar o arquivo** fisicamente.
4. **Confirmar preço e custo** de cada SKU do AW26.
5. **Ler o EMQ** no Gerenciador de Eventos.

Com (1) e (2) em mãos, o plano deixa de ter qualquer 🔴 na matemática. Todo o raciocínio estratégico — arquivo como alavanca de ticket em vez de destino de mídia, campanha única em vez de fragmentada, canais gratuitos antes do pago — **não depende desses números** e permanece válido.
