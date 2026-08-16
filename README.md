# BVBA Supply® — repositório consolidado

Este branch reúne **todos os projetos** que estavam espalhados em branches
separadas do `bvba-qa`. Antes, cada sessão do Claude terminava numa branch
própria e o `main` ficava com um README de uma linha; para ver tudo era
preciso saber os quatro nomes de branch de cor. Agora um `git clone` só traz
o repositório inteiro.

Os branches originais **continuam intactos** — nada foi apagado nem
reescrito. Esta branch é a soma deles.

---

## Os quatro projetos

| # | Projeto | Onde está | O que é |
|---|---|---|---|
| 1 | **Agente de drop — Nuvemshop** | [`README-agente-drop.md`](README-agente-drop.md) · `agente_drop/` `catalogo/` `testes/` | Código Python. Sobe o drop como rascunho e publica tudo no horário. 156 testes, sem dependências. |
| 2 | **Plano de marketing** | [`PLANO.md`](PLANO.md) · [`plano-360/`](plano-360/) | Documentação operacional. Plano v2 (mídia zerada) + os 10 documentos de apoio do plano 360. |
| 3 | **QA das imagens de e-commerce** | [`AVALIACAO_OUTPUTS_ECOMMERCE.md`](AVALIACAO_OUTPUTS_ECOMMERCE.md) | Auditoria do acervo Magnific contra a regra de IA da marca. |
| 4 | **Pesquisa — economia prateada** | [`pesquisa/economia-prateada-negocios-50-mais.md`](pesquisa/economia-prateada-negocios-50-mais.md) | Pesquisa de mercado sobre negócios para o público 50+. Não é sobre a BVBA. |

Contexto de marca e regras que valem para tudo: [`CLAUDE.md`](CLAUDE.md).
Estado da última sessão de marketing: [`HANDOFF.md`](HANDOFF.md).

Para abrir tudo isto como um vault Obsidian sincronizado entre PCs:
[`SINCRONIA-OBSIDIAN.md`](SINCRONIA-OBSIDIAN.md).

---

## 1 · Agente de drop (o único que é código)

```bash
python3 -m unittest discover -s testes -t .   # 156 testes, ~10s, sem rede
python3 -m agente_drop validar                # confere o catálogo sem tocar na loja
```

Manual completo em [`README-agente-drop.md`](README-agente-drop.md).

> **Estado real do catálogo:** `python3 -m agente_drop validar` acusa hoje
> **55 erros e 11 avisos** — as 11 peças do AW 2026 estão sem preço e sem
> foto. Isso é pendência de conteúdo, não bug: o caminho para resolver está
> em [`catalogo/PENDENTE.md`](catalogo/PENDENTE.md) (preencher
> `catalogo/pendencias.txt` e rodar `python3 ferramentas/preencher.py`).

## 2 · Plano de marketing

Leia nesta ordem: [`PLANO.md`](PLANO.md) (o plano vigente, sem orçamento de
mídia) → [`plano-360/08-contexto-consolidado.md`](plano-360/08-contexto-consolidado.md)
(tem precedência onde houver conflito) →
[`plano-360/07-fontes-e-proveniencia.md`](plano-360/07-fontes-e-proveniencia.md)
(classifica cada número por origem).

`plano-360/` é material de apoio: a copy, os scripts de WhatsApp e o
checklist de medição seguem válidos; a arquitetura de mídia paga, não.

## 3 · QA das imagens

[`AVALIACAO_OUTPUTS_ECOMMERCE.md`](AVALIACAO_OUTPUTS_ECOMMERCE.md) declara na
abertura a própria limitação: é auditoria do **registro de produção**
(prompts, modelos, custos), não QA visual — a rede da sessão bloqueava os
hosts das imagens. Leia a seção 0 antes de agir nas conclusões.

## 4 · Pesquisa da economia prateada

Trabalho independente da BVBA, guardado aqui por conveniência.

---

## De onde veio cada coisa

| Branch de origem | Trouxe |
|---|---|
| `claude/bvba-autonomous-agent-lwnadl` | agente de drop, catálogo, testes, workflows |
| `claude/bvba-360-marketing-plan-xv9rux` | `PLANO.md`, `plano-360/`, `CLAUDE.md`, `HANDOFF.md` |
| `claude/bvba-ecommerce-image-outputs-y9nfvc` | `AVALIACAO_OUTPUTS_ECOMMERCE.md` |
| `claude/business-senior-50-plus-csbmvr` | `pesquisa/` |

Só dois arquivos precisaram de decisão na junção:

- **`.gitignore`** — as duas versões foram unidas. A regra `.env.*` do plano
  de marketing engoliria o `.env.exemplo` do agente, então há um `!.env.exemplo`
  explícito preservando o modelo (que não tem segredo nenhum).
- **`README.md`** — o do agente virou `README-agente-drop.md`, com todos os
  links relativos ainda válidos, e a raiz passou a ser este índice.

Nenhum arquivo dos quatro projetos foi movido de lugar ou editado no
conteúdo.

---

## Trazendo para a sua máquina

```bash
git clone https://github.com/vicdeleao1997-arch/bvba-qa.git
cd bvba-qa
git checkout claude/trazer-projetos-pc-0vlyki
claude
```

O `CLAUDE.md` carrega sozinho e traz o contexto da marca.
