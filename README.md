# BVBA Supply®

Todos os projetos da marca num lugar só. Um `git clone` traz o repositório
inteiro — não existe mais branch escondida com metade do trabalho.

As duas máquinas (MacBook e desktop Windows 11) ficam **em sincronia sozinhas**,
a cada 15 minutos, pelo GitHub. Como ligar isso está em
[`sinc/README.md`](sinc/README.md).

```
   MacBook  ──┐                    ┌──  Desktop Windows 11
  (launchd)   ├──►  GitHub  ◄──────┤   (Agendador de Tarefas)
   15 em 15   ┘                    └──   15 em 15
```

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

## Sincronia entre as duas máquinas

Manual completo em [`sinc/README.md`](sinc/README.md). O essencial:

```bash
git clone https://github.com/vicdeleao1997-arch/bvba-qa.git
cd bvba-qa

./sinc/instalar-macos.sh          # MacBook
```
```powershell
.\sinc\instalar-windows.ps1       # desktop Windows 11
```

Depois disso, nada. As duas máquinas se acertam a cada 15 minutos.

Três coisas a sincronia **não** faz, de propósito: não deixa dado de cliente
entrar no Git, não publica código com teste quebrado, e não resolve conflito
sozinha sobrescrevendo — ela para e avisa. Nenhum `--force` existe nesse código.

O que fica de fora: cofre do Obsidian, fotos do Drive, base de telefones e o
`.env` de cada máquina. Isso é escolha, não esquecimento — a tabela em
[`sinc/README.md`](sinc/README.md) diz quem cuida de cada um.

---

## De onde veio cada coisa

Cada projeto nasceu numa branch própria. Todas foram unidas no `main` (PR #5);
as originais continuam intactas, nada foi apagado nem reescrito.

| Branch de origem | Trouxe |
|---|---|
| `claude/bvba-autonomous-agent-lwnadl` | agente de drop, catálogo, testes, workflows |
| `claude/bvba-360-marketing-plan-xv9rux` | `PLANO.md`, `plano-360/`, `CLAUDE.md`, `HANDOFF.md` |
| `claude/bvba-ecommerce-image-outputs-y9nfvc` | `AVALIACAO_OUTPUTS_ECOMMERCE.md` |
| `claude/business-senior-50-plus-csbmvr` | `pesquisa/` |

Nenhum arquivo dos quatro projetos foi movido de lugar. Só três precisaram de
decisão:

- **`.gitignore`** — as duas versões unidas. A regra `.env.*` do plano de
  marketing engoliria o `.env.exemplo` do agente, então há um `!.env.exemplo`
  explícito preservando o modelo (que não tem segredo nenhum).
- **`README.md`** — o do agente virou `README-agente-drop.md`, com os links
  relativos ainda válidos, e a raiz passou a ser este índice.
- **`catalogo/produtos.csv`** — estava versionado em CRLF, o que faria o Mac e o
  Windows brigarem a cada sincronia. Convertido para LF, dados conferidos linha
  a linha. O [`.gitattributes`](.gitattributes) impede que volte a acontecer.
