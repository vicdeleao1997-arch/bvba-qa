# Handoff — continuar na sessão local

Fechamento da sessão remota de **11/08/2026**. Este documento existe para a próxima sessão local começar produzindo, sem redescobrir nada.

> **Atualizado em 16/08/2026.** O que este handoff descrevia como "a branch do plano" agora está no `main`, junto com os outros três projetos ([#5](https://github.com/vicdeleao1997-arch/bvba-qa/pull/5)). E não existe mais "a próxima sessão no Mac": o MacBook e o desktop Windows 11 ficam em sincronia sozinhos, a cada 15 minutos — ver [`sinc/README.md`](sinc/README.md).

Leia antes: [`CLAUDE.md`](CLAUDE.md) (contexto e regras da marca) e [`plano-360/08-contexto-consolidado.md`](plano-360/08-contexto-consolidado.md) (a operação real, com precedência sobre os demais).

---

## Como retomar

```bash
git clone https://github.com/vicdeleao1997-arch/bvba-qa.git
cd bvba-qa
claude
```

O `CLAUDE.md` carrega sozinho e o `main` já traz os quatro projetos — não há branch a lembrar. O [#4](https://github.com/vicdeleao1997-arch/bvba-qa/pull/4), que este documento citava como aberto, foi fechado depois que seu conteúdo entrou no `main`; a branch original segue intacta.

Se esta for a primeira vez nesta máquina, ligue a sincronia uma vez — depois disso ela cuida de si:

```bash
./sinc/instalar-macos.sh          # MacBook
```
```powershell
.\sinc\instalar-windows.ps1       # desktop Windows 11
```

---

## ✅ Entregue

| Item | Onde |
|---|---|
| Plano 360 completo — 9 documentos | [`plano-360/`](plano-360/) |
| Auditoria de procedência de cada dado | [`plano-360/07-fontes-e-proveniencia.md`](plano-360/07-fontes-e-proveniencia.md) |
| Contexto real consolidado (campanha em curso, preços, volume) | [`plano-360/08-contexto-consolidado.md`](plano-360/08-contexto-consolidado.md) |
| Plano visual publicado | [artifact](https://claude.ai/code/artifact/17472729-640d-44bf-a71b-f3da332899d8) · fonte em `plano-360/plano-bvba-artifact.html` |
| Contexto permanente da marca | [`CLAUDE.md`](CLAUDE.md) |
| Proteção contra vazamento de dados de cliente | [`.gitignore`](.gitignore) |
| Verificação: pasta "FUNDO BRANCO v2" está vazia | `plano-360/qa-fotos-lote-A.csv` e `-B.csv` |

### Achados que mudaram o plano

1. **A loja faz ~2–3 pedidos/mês.** O plano de lançamento de 02/08 registra que 8 pedidos seriam *"mais que o trimestre inteiro"*. Com R$900/mês de mídia, o **ROAS real é ~0,4** — prejuízo de ~R$700/mês.
2. **Preços reais:** R$129,90 a peça · R$219 duas · R$299 três. Camiseta e boné custam o mesmo. Ticket atual **R$132**.
3. **Correção minha:** eu havia acusado a conta da BVBA de rotação excessiva de criativo. Era falso — os e-mails de aprovação eram majoritariamente de outras contas na mesma caixa (Instituto O Setor Elétrico, CIDE, GTP Telles). **Filtre sempre pelo ID `321768910427826`.**
4. **A pasta "FUNDO BRANCO — FINAL v2 (97 fotos · Magnific)" está vazia** — só um stub de 160 bytes (JPEG 1×1 preto). O upload do Magnific abortou. A pasta irmã v1 tem 97 arquivos, mas é o shooting on-model em ciclorama cinza, não packshot recortado.

---

## ⏳ Não concluído — tarefas para a sessão local

Cinco agentes ficaram em execução quando a sessão fechou. **Todo esse trabalho é mais fácil no Mac**, com rede aberta e acesso ao Drive pelo Finder. Estão em ordem de impacto.

### 1. Auditoria das imagens do acervo Magnific 🔴 é o que você pediu

**Por que travou aqui:** `download_file_content` devolve a imagem em base64 dentro do contexto — um PNG de 5 MB vira ~1,7 milhão de tokens. Inviável remotamente. **No Mac, é só baixar a pasta do Drive e abrir os arquivos localmente.**

Pastas a auditar:
- `BVBA_MAGNIFIC_HISTORICO / Imagens ecomm magnific` — `1evrmpY1hfCu7WMkP5XHw_7HVoyfKxY_H`
- `BVBA_MAGNIFIC_HISTORICO / 03_ecomm_produtos_desktop` — `1MsnUOdw-whg2XWSWpythVGdu-sgtKn3G`
- A pasta com os `magnific_*.png` — `16osx6ct1Zvpnd4r6zvgyK01yhWnJCRCG`

**O critério de reprovação é a própria regra da marca:** *"peça real, nunca regenerada; só o ambiente é gerado por IA."* Vários arquivos têm o prompt no nome — `magnific__photo-a-black-tshirt-with-a-white-graphic-logo-on-__73304.png`, `magnific__candid-editorial-ecommerce-fashion-photo-waistup-__73296.png`. Se a peça foi gerada, está fora da política, não só com defeito estético.

Procurar: logo do gato deformado, estampa ilegível, anatomia errada, textura alucinada, halo de recorte, manga ou barra amputada, fundo sujo. Saída em `plano-360/qa-imagens-magnific.csv` com `arquivo · veredito · defeito · gravidade · onde · acao`.

Depois: **cruzar com o que está publicado na loja** e despublicar as reprovadas na Nuvemshop — isso só dá para fazer localmente.

### 2. Normalizar a base de telefones para E.164

`Fonte clientes BVBA 04.2024.csv` (Drive, id `19MldHKBQ2wC34x2Ra1iNSDvNttr8sQXG`). Formato atual `+55 11 99999-9999` quebra o casamento do Público Personalizado no Meta.

Regras: remover não-dígitos; Portugal (`351`) mantém 9 dígitos; Brasil → tirar o `55`, validar DDD 11–99; 8 dígitos começando em 6–9 é celular antigo e **falta o nono dígito** (inserir `9` e marcar); 8 dígitos começando em 2–5 é fixo; remover duplicatas (o arquivo tem um bloco inteiro repetido).

Gerar `phone`-only para upload no Meta + um CSV de auditoria. **Salvar só no Drive — nunca no repositório** (o `.gitignore` bloqueia, mas confira).

### 3. Planilha operacional

`BVBA-Painel-Operacional-AW26.xlsx` com: estoque do arquivo, calculadora de margem/CAC/ROAS com tabela de sensibilidade, painel semanal, UTMs e pipeline de criativos. **Use os preços reais** (R$129,90 · R$219 · R$299), não as estimativas dos documentos 01–06.

### 4. Criativos

Banner "Arquivo Aberto", Stories do Vault e do drop, card de guia de tamanho, post de feed. Método que funciona: **HTML renderizado com Playwright** (tipografia correta; modelo de imagem erra texto), compondo fotos reais do shooting. Cartela nas fichas técnicas: off-white `#f2efeb`, bege `#c1a37f`, cinza claro `#e0e0e0`.

### 5. Calendário e modelos de e-mail

Eventos do cronograma no Google Calendar + 5 rascunhos no Gmail (Archive Vault, VIP AW26, e os três de carrinho abandonado). Rascunhos endereçados a `contato@bvbasupply.com.br` e com assunto começando em `[MODELO]`, para não haver risco de disparo acidental.

---

## 🎯 As decisões que valem mais que qualquer entregável

Em ordem:

1. **Exportar os pedidos da Nuvemshop** (12 meses, CSV). Resolve de uma vez AOV, ticket, mix, recompra e sazonalidade — hoje tudo inferido. **Maior impacto da lista.**
2. **Exportar o relatório da Meta** (90 dias, por campanha/conjunto/anúncio, com gasto, compras e valor de conversão). Dá o ROAS real.
3. **Ler o resultado da janela VIP de 10–13/08**, que acabou de rodar.
4. **Decidir sobre a mídia:** manter R$30/dia ou pausar 60 dias e redirecionar para estoque de brinde e conteúdo. A aritmética favorece pausar.
5. **Trocar o brinde de "posição na fila" para "tamanho de carrinho"** (a partir de 2 peças). Custo zero, puxa o ticket de R$132 para R$219, e elimina a disputa de status entre quem comprou com minutos de diferença.
6. **Validar CAPI e EMQ ≥ 7** na Nuvemshop — bloqueante para qualquer mídia paga.

---

## Acompanhar e comandar pelo app

Vale entender o trade-off, porque ele é real:

| | Sessão local (Mac) | Sessão remota (app) |
|---|---|---|
| Nuvemshop, Meta, site, Obsidian | ✅ | ❌ egresso 403 |
| Visível e comandável pelo celular | ❌ terminal do Mac | ✅ claude.ai/code |

**Hoje não dá para ter os dois na mesma sessão** — e a causa não é permissão, é a política de rede do ambiente remoto, que nega tudo por padrão.

**O caminho para ter os dois:** alterar a política de rede do ambiente em [claude.ai/code](https://claude.ai/code), liberando `*.nuvemshop.com.br` e `graph.facebook.com`. Feito isso, uma sessão remota alcança as plataformas **e** continua comandável pelo celular. Referência: [code.claude.com/docs/en/claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web). Ainda serão necessários os tokens de API de cada plataforma.

**Enquanto isso, o arranjo prático:** trabalho de plataforma (despublicar foto, subir campanha, exportar pedidos) na sessão local do Mac; planejamento, redação, Drive, Gmail, Calendar e commits em sessão remota pelo app. Este repositório é o ponto de encontro dos dois — tudo que importa está versionado.

Também dá para agendar tarefas recorrentes que disparam sozinhas numa sessão remota (Routines) — por exemplo, um relatório semanal dos cinco números do painel toda segunda de manhã. É só pedir e eu configuro.
