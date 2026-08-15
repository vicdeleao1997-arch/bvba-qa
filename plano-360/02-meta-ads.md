# 02 — Meta Ads: estrutura, configuração e regras de operação

Conta: **CA - BVBA SUPPLY (321768910427826)** · Orçamento: **R$30/dia** (teto)

---

## 1. A estrutura (exatamente isto, nada além)

```
CAMPANHA:  BVBA | Vendas | AW26
├─ Objetivo:        Vendas
├─ Otimização:      Compra (nunca "Adicionar ao carrinho" ou "Clique no link")
├─ Orçamento:       CBO — Advantage+ Campaign Budget — R$30/dia
├─ Estratégia:      Maior volume (sem custo-alvo no início)
│
└─ CONJUNTO:  AW26 | Amplo BR
   ├─ Público:      Advantage+ Audience (sem sugestões travadas)
   ├─ Local:        Brasil
   ├─ Idade:        18–40
   ├─ Gênero:       Todos
   ├─ Posicionam.:  Advantage+ (automáticos — todos)
   ├─ Exclusões:    NENHUMA no início
   │
   └─ 5 ANÚNCIOS (os 5 ângulos de 03-criativos-e-copy.md)
      ├─ 01 · Demonstração — calça conversível
      ├─ 02 · UGC — caimento oversized
      ├─ 03 · Arquivo — escassez
      ├─ 04 · Explicador — guia de tamanho
      └─ 05 · Lifestyle — shooting 25/07
```

**Uma campanha. Um conjunto. Cinco anúncios.** Isso é a estrutura inteira.

---

## 2. As decisões de configuração, e o porquê de cada uma

### Por que otimizar por Compra, e não por evento intermediário

É tentador otimizar por "Adicionar ao carrinho" quando o volume de compras é baixo — o algoritmo teria mais eventos para trabalhar. **Não faça.** O Meta vai entregar para pessoas que adicionam ao carrinho e não compram, porque foi exatamente isso que você pediu. Com R$30/dia, cada real precisa perseguir a única métrica que paga a conta.

### Por que nenhuma exclusão no início

O reflexo é excluir compradores dos últimos 30 dias da prospecção. Com o volume da BVBA, a lista de compradores tem algumas dezenas de pessoas — excluí-la não muda a entrega, mas **adiciona uma restrição** que o algoritmo precisa respeitar num orçamento que já é apertado.

Reavaliar quando passar de 100 compras/mês.

### Por que Advantage+ Audience e não público de interesses

Segmentar por interesse ("streetwear", "skate", "Supreme") parece controle, mas em 2026 funciona como **dica**, não como cerca. Um público de interesse estreito com R$30/dia entrega para o mesmo pequeno grupo repetidamente — a frequência dispara, o CTR desaba e o custo sobe em duas semanas.

Amplo com Advantage+ dá espaço para o algoritmo achar o comprador. E o criativo faz a segmentação: quem para num Reel de calça oversized conversível **se auto-seleciona** melhor do que qualquer caixa de interesse.

### Por que Brasil inteiro e não só Sudeste

Concentrar geografia com orçamento baixo tem lógica (menos dispersão), mas os dados da própria BVBA contradizem: a base de clientes de 2024 tem contatos de **RJ, SP, MG, ES, SC, PR, RS, BA, CE, PE, GO, DF, PA, MA — e até Portugal**. A demanda é nacional. Restringir a SP cortaria a maior parte da base comprovada.

### Por que CBO e não orçamento por conjunto

Com um único conjunto, CBO e ABO dão no mesmo — mas CBO já deixa a estrutura pronta para quando o segundo conjunto entrar, sem precisar reconstruir a campanha (o que zeraria o aprendizado).

---

## 3. Regras de operação — o protocolo anti-sabotagem

O padrão observado na conta (4 anúncios aprovados no mesmo dia, várias vezes por semana) é o principal destruidor de performance. **Toda edição estrutural reinicia a fase de aprendizado.** Com R$30/dia, uma campanha que reinicia o aprendizado toda semana nunca chega a lugar nenhum.

### As regras

| Regra | Detalhe |
|---|---|
| 🔒 **Sete dias de silêncio** | Depois de publicar, **não toque na campanha por 7 dias.** Não pausar anúncio, não editar copy, não mudar orçamento, não trocar criativo. Nem para "só ajustar uma coisinha" |
| 📊 **Não leia resultado diário** | Um dia sem venda a R$30/dia é ruído estatístico, não sinal. A leitura é semanal |
| 💰 **Orçamento muda no máximo 20%** | E no máximo a cada 3–4 dias. Mudanças maiores reiniciam o aprendizado |
| 🎨 **Criativo novo entra, o antigo não sai** | Adicionar anúncio a um conjunto ativo perturba menos que trocar. Deixe o Meta redistribuir |
| ⏸️ **Só pause o que teve chance real** | Nada de pausar anúncio com menos de R$50 gastos. Abaixo disso, os dados não significam nada |

### A leitura semanal (toda segunda, 15 minutos)

| Métrica | Sinal verde | Alerta | Ação |
|---|---|---|---|
| ROAS | ≥ 2,5 | < 1,75 | Ver tabela de decisão abaixo |
| CPA | ≤ R$90 | > R$148 | Acima do teto de lucro bruto — revisar oferta |
| CTR | ≥ 1,2% | < 0,8% | Criativo fraco — trocar o hook |
| Frequência | ≤ 2,0 | > 2,5 | Fadiga — rodada nova de criativo |
| CPM | ≤ R$40 | > R$60 | Público pequeno demais ou criativo com baixo engajamento |

### Tabela de decisão (definida agora, para não decidir com o emocional depois)

| Após 14 dias / R$420 gastos | Decisão |
|---|---|
| ROAS ≥ 3,0 | **Escalar.** +20% a cada 3–4 dias. Monitorar CPA por 48h após cada aumento |
| ROAS 2,0 – 3,0 | **Manter orçamento.** Trabalhar AOV e criativo. Não mexer no budget |
| ROAS 1,75 – 2,0 | **Manter e diagnosticar.** Provável problema de página ou de ticket, não de mídia |
| ROAS < 1,75 | **Pausar o paid.** O problema é oferta/página. Voltar ao orgânico, consertar, religar |

**Se pausar:** não é fracasso, é economia. R$900/mês em mídia que não paga é R$900 que poderia ter virado a produção do próximo drop.

---

## 4. Escala — o que fazer quando funcionar

**Escala vertical (subir orçamento):** +15–20% a cada 3–4 dias. Se o CPA subir mais de 25% nas 48h seguintes, **volte ao valor anterior e espere 72h**. Subir de R$30 para R$60 de uma vez joga a campanha de volta ao aprendizado.

**Escala horizontal (novos criativos):** mais estável que a vertical, e mais barata. Antes de subir orçamento, esgote os ângulos criativos — normalmente há mais ganho em achar um segundo criativo vencedor do que em dobrar o orçamento no primeiro.

**Ordem recomendada de escala:**
1. Novos criativos dentro do conjunto atual (R$0 de risco adicional)
2. Orçamento +20%, com 3–4 dias de observação
3. Segundo conjunto de retargeting — **só acima de 1.500 visitantes/mês**
4. ASC (Advantage+ Shopping) — **só acima de 30 compras/semana**

---

## 5. Catálogo e integrações da Nuvemshop (fazer antes de lançar)

| Integração | Custo | Impacto |
|---|---|---|
| **Catálogo do Meta** conectado à Nuvemshop | R$0 | Habilita anúncios dinâmicos e melhora o sinal de produto. **Faça** |
| **CAPI** (Conversions API) nativa da Nuvemshop | R$0 | **Bloqueante.** Ver `06-medicao-e-checklist.md` |
| **Listagens gratuitas do Google Shopping** (Merchant Center) | R$0 | Alcance incremental sem mídia. **Faça** |
| Instagram Shopping / marcação de produtos | R$0 | Transforma cada post em vitrine. **Faça** |

Todas as quatro são gratuitas e todas melhoram o resultado do R$30/dia sem consumir um centavo dele.

---

## 6. Uma nota sobre o provador virtual (Sizebay)

A Sizebay entrou em contato em 21/07 oferecendo provador com IA. **O timing é relevante:** a objeção nº1 em moda online é tamanho — e o AW26 é inteiramente oversized boxy, uma modelagem que o cliente não sabe traduzir para o próprio corpo. Isso gera carrinho abandonado e, pior, troca (que come margem duas vezes).

**Recomendação:** não contrate agora. Primeiro resolva de graça — o anúncio nº 04 (`03-criativos-e-copy.md`) é exatamente um explicador de caimento com tabela de medidas, e as fichas técnicas do AW26 têm as tabelas prontas para preencher. Meça a taxa de troca por 60 dias. Se a troca por tamanho passar de 8% dos pedidos, aí a Sizebay se paga — e você negocia com dado na mão, não com promessa.
