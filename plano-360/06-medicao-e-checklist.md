# 06 — Medição e checklist de lançamento

> **Com R$30/dia, sinal ruim de conversão não é um detalhe técnico — é o orçamento inteiro desperdiçado.** Uma conta com medição precisa entrega substancialmente mais que a mesma conta com medição quebrada, pelo mesmo dinheiro. Este é o documento mais importante do plano.

---

## 1. Meta — Pixel + CAPI (bloqueante)

A Nuvemshop tem integração nativa com a Conversions API do Meta. Rodar **só o Pixel** (navegador) perde eventos para bloqueadores, iOS e cookies de terceiros. Pixel + CAPI juntos, com deduplicação, recuperam essa perda.

### Configuração

| Item | Alvo | Onde |
|---|---|---|
| Pixel ativo | ✅ | Nuvemshop → Marketing → Meta |
| **CAPI ativa** | ✅ | Mesma tela — ative a Conversions API |
| Deduplicação por `event_id` | ✅ | Automática na integração nativa |
| **EMQ (Event Match Quality)** | **≥ 7** | Gerenciador de Eventos → Fontes de Dados |
| Valor de conversão passando | ✅ | Evento Purchase precisa mandar `value` e `currency` |
| Catálogo conectado | ✅ | Commerce Manager |

### Como subir o EMQ (isto é o que mais move o ponteiro)

O EMQ mede o quanto os eventos casam com pessoas reais. Quanto mais identificadores você manda, melhor o casamento — e melhor a entrega, pelo mesmo orçamento.

Garanta que estão sendo enviados: **e-mail, telefone, `external_id`, `fbp`, `fbc`, IP e user agent.**

Formatação — erro aqui quebra o casamento mesmo com o dado presente:
- Tudo com hash **SHA-256** (a integração da Nuvemshop faz automaticamente)
- Nomes em **minúsculo**, sem acento
- Telefone em **E.164**: `+5511999999999` — com código do país, sem parênteses, traço ou espaço

> O CSV da base de clientes está com telefones no formato `+55 11 99999-9999`. **Normalize para E.164 antes de subir como público personalizado** — senão o casamento despenca e o público sai muito menor do que deveria.

### Validação (faça antes de gastar o primeiro real)

1. Faça uma **compra-teste real** de R$1 na loja
2. Abra Gerenciador de Eventos → Testar Eventos
3. Confirme:
   - [ ] Evento `Purchase` aparece em menos de 2 minutos
   - [ ] Aparece **uma vez só** (se aparecer duas, a deduplicação está quebrada)
   - [ ] Traz `value` e `currency: BRL`
   - [ ] Origem mostra "Navegador e servidor"
4. Espere 72h e confira o **EMQ**. Abaixo de 7, revise os identificadores antes de lançar.

---

## 2. Públicos personalizados (subir agora, usar depois)

Mesmo sem campanha de retargeting ativa, esses públicos precisam começar a acumular desde já:

| Público | Origem | Uso futuro |
|---|---|---|
| **Compradores BVBA** | CSV de 500 contatos (E.164) + compras do Pixel | Base de Lookalike + exclusão quando escalar |
| Visitantes 180 dias | Pixel | Retargeting quando passar de 1.500 visitas/mês |
| Carrinho abandonado 30 dias | Pixel | Retargeting |
| Engajamento IG/FB 365 dias | Nativo | Prospecção morna |
| **Lookalike 1% de compradores** | Do público de compradores | Prospecção — só com 100+ na origem |

**Importante:** o Lookalike precisa de pelo menos ~100 pessoas casadas na origem. A base de 500 telefones, bem normalizada, deve casar em torno de 60–70% — o suficiente.

---

## 3. Google — gratuito apenas

Não haverá Google Ads pago neste ciclo (justificativa em `02-meta-ads.md`). Mas duas coisas gratuitas devem ser ligadas:

| Item | Custo | Ação |
|---|---|---|
| **Listagens gratuitas do Shopping** | R$0 | Nuvemshop → Google Shopping → conectar Merchant Center |
| **GA4** | R$0 | Instalar e marcar `purchase` como evento-chave |
| Perfil da Empresa no Google | R$0 | Já existe (54 visualizações em julho) — atualizar fotos e link da loja |

---

## 4. UTMs — padrão único

Sem padrão de UTM, o relatório de canais vira lixo em duas semanas. Use exatamente este formato:

```
?utm_source=[origem]&utm_medium=[meio]&utm_campaign=[campanha]&utm_content=[criativo]
```

| Canal | Exemplo |
|---|---|
| Meta Ads | `?utm_source=meta&utm_medium=paid&utm_campaign=aw26&utm_content=calca_conversivel` |
| Instagram bio | `?utm_source=instagram&utm_medium=bio&utm_campaign=aw26` |
| Stories orgânico | `?utm_source=instagram&utm_medium=stories&utm_campaign=aw26` |
| WhatsApp Vault | `?utm_source=whatsapp&utm_medium=crm&utm_campaign=archive_vault` |
| WhatsApp AW26 | `?utm_source=whatsapp&utm_medium=crm&utm_campaign=aw26_vip` |
| E-mail | `?utm_source=email&utm_medium=crm&utm_campaign=aw26` |

Sempre minúsculo, sempre sem acento, sempre com underline. Um `Meta` e um `meta` viram duas linhas diferentes no relatório.

---

## 5. ✅ CHECKLIST BLOQUEANTE — não subir campanha sem isto

### Medição
- [ ] Pixel ativo e disparando
- [ ] **CAPI ativa e deduplicada**
- [ ] **EMQ ≥ 7** nos eventos-chave
- [ ] Evento `Purchase` com `value` e `currency`
- [ ] Compra-teste validada (aparece 1× em < 2 min)
- [ ] GA4 instalado
- [ ] Padrão de UTM aplicado em todos os links

### Loja
- [ ] Estoque de arquivo **recontado** por peça e tamanho
- [ ] Preços do AW26 confirmados e publicados
- [ ] Todas as peças do AW26 com foto do shooting editado
- [ ] **Tabela de medidas em toda página de produto** (mata a objeção nº1)
- [ ] Categoria oculta "Archive Vault" criada
- [ ] Bônus "Arquivo Aberto" configurado e visível no carrinho
- [ ] Barra de progresso do carrinho ativa
- [ ] Order bump do chaveiro no checkout
- [ ] Frete grátis acima de R$199 funcionando
- [ ] Pix com 5% off funcionando
- [ ] Carrinho abandonado configurado (1h / 24h / 72h)
- [ ] Loja testada no celular — **a maior parte do tráfego do Meta é mobile**

### Meta
- [ ] Catálogo conectado e sincronizado
- [ ] Instagram Shopping ativo
- [ ] Públicos personalizados criados
- [ ] CSV de clientes normalizado em E.164 e subido
- [ ] Campanha montada conforme `02-meta-ads.md`
- [ ] 5 criativos prontos, com legenda embutida no vídeo
- [ ] Copy revisada (sem erro de português — mata credibilidade na hora)

### Operação
- [ ] WhatsApp Business configurado com etiquetas
- [ ] Base de 500 contatos limpa e segmentada
- [ ] Cartão com QR da Lista VIP impresso
- [ ] Embalagem e etiquetas em estoque para o volume esperado
- [ ] **Emissão de NF-e testada** (o e-CNPJ A1 foi emitido em jun/2026 — validar que está instalado e funcionando na Nuvemshop)

---

## 6. Painel semanal — os 5 números de toda segunda-feira

| # | Métrica | Alvo | Onde |
|---|---|---|---|
| 1 | **Receita total** (separada por canal via UTM) | Crescente | Nuvemshop + GA4 |
| 2 | **AOV** | **R$260** | Nuvemshop |
| 3 | **ROAS do Meta** | ≥ 2,5 | Gerenciador |
| 4 | **CPA** | ≤ R$148 (ideal ≤ R$90) | Gerenciador |
| 5 | **Peças de arquivo liquidadas** | 114 → 0 em 90 dias | Planilha |

**O AOV é o número-mestre.** Se ele não subir de ~R$160 para ~R$260, o teto de CAC continua em R$91 e a mídia paga não fecha a conta em nenhum cenário. Todos os outros números dependem dele.

---

## 7. Os erros que matariam este plano

| Erro | Consequência |
|---|---|
| Ligar o paid antes do EMQ ≥ 7 | Orçamento inteiro entregue para o público errado |
| Mexer na campanha nos primeiros 7 dias | Aprendizado reinicia — as 2 primeiras semanas viram desperdício |
| Dividir R$30/dia em 3 conjuntos | Nenhum sai do aprendizado. Pior cenário possível |
| Dar 20% off na vitrine pública | Destrói o preço de referência e não muda o comportamento de compra |
| Anunciar o arquivo com mídia paga | Paga-se para vender o que o mercado já recusou a preço cheio |
| Ler resultado diário e reagir | Ruído estatístico vira decisão ruim |
| Disparar 500 WhatsApps de uma vez | Número bloqueado, base perdida |
| Publicar sem tabela de medidas | Carrinho abandonado e troca — que come margem duas vezes |
