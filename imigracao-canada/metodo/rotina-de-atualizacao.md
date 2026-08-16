# Rotina de atualização

O pedido foi "sempre se atualize com todos os programas de imigração do governo
canadense". Regra canadense muda por *Ministerial Instruction*, publicada sem
aviso e com efeito quase imediato — três mudanças relevantes só em 2026
(SOWP em janeiro e em março, reforma do OINP em maio/junho/agosto). Base
desatualizada em imigração não é imprecisão: é decisão errada com custo real.

---

## Onde rodar

| Ambiente | Alcança fonte oficial? |
|---|---|
| **Sessão local no Mac** | ✅ Sim — é o modo correto de atualizar |
| Sessão remota (nuvem) | ❌ `canada.ca` e `ontario.ca` devolvem 403 no proxy. Só busca web, que traz fonte secundária |

Vale a mesma regra do [`CLAUDE.md`](../../CLAUDE.md): rodar local por padrão.
Se a atualização for feita em sessão remota, marcar as linhas afetadas em
[`../FONTES.md`](../FONTES.md) como **secundária** e deixar pendente a
conferência.

---

## Cadência

| Frequência | O que checar |
|---|---|
| **Semanal** | Resultados de draw do Express Entry (data, categoria, corte, nº de ITAs) |
| **Semanal** | Draws de EOI do OINP — a rota abriu em 04/08/2026 e ainda não há histórico de cortes |
| **Mensal** | Fase 2 do OINP: saúde prioritária, empreendedor, talento excepcional |
| **Mensal** | Mudanças de regra do PGWP e do SOWP |
| **Trimestral** | Grade do CRS, proof of funds, taxas, prazos de processamento |
| **Anual** | Plano de Níveis de Imigração e alocação de nomeações de Ontário |
| **Sempre** | Antes de qualquer submissão ou pagamento |

---

## Fontes, em ordem de autoridade

**Primárias — só elas decidem**

- `canada.ca/en/immigration-refugees-citizenship` — IRCC
- `canada.ca/.../express-entry/submit-profile/rounds-invitations.html` — resultados de draw
- `ontario.ca/page/ontario-workforce-priority-stream` — OWPS
- `ontario.ca/page/ontario-immigrant-nominee-program-oinp-employer-guide` — guia do empregador
- `noc.esdc.gc.ca` — NOC/TEER
- `jobbank.gc.ca` — mediana salarial por ocupação e região

**Secundárias — úteis para detectar mudança, nunca para decidir**

CIC News · Fragomen · Gowling WLG · Green & Spiegel · Erickson Immigration ·
Fakhoury Law Group · Moving2Canada

Fonte secundária serve para **descobrir que algo mudou**. A confirmação é
sempre na primária.

---

## Procedimento

1. Rodar as buscas da cadência devida
2. Comparar com o que está em [`../programas/`](../programas/)
3. Mudou algo? Atualizar o arquivo **e** a linha correspondente em
   [`../FONTES.md`](../FONTES.md), com data nova
4. Se a mudança afeta a rota escolhida, recalcular o CRS e revisar
   [`../processo/plano-de-acao.md`](../processo/plano-de-acao.md)
5. Registrar no log abaixo
6. Commitar com mensagem no formato `imigração: atualiza <arquivo> — <o que mudou>`

### Gatilhos de recálculo imediato

- Corte de draw se move mais de 20 pontos
- Categoria de draw criada ou removida
- Mudança na grade do CRS
- Qualquer publicação de regra da fase 2 do OINP
- Primeiro histórico de corte de EOI do OWPS
- Aniversário de 30 anos de qualquer um dos dois (−5 de CRS)
- Casamento formalizado (muda a coluna do cálculo: com/sem cônjuge)

---

## Log de atualizações

| Data | Quem | O que mudou | Ambiente |
|---|---|---|---|
| 16/08/2026 | Claude (sessão remota) | Base criada. OWPS aberto em 04/08/2026 mapeado; Express Entry 2026; PGWP/SOWP; rotas descartadas | Remoto — **fontes secundárias, conferência oficial pendente** |
