# Agente de drop — BVBA na Nuvemshop

Agente autonomo que sobe os produtos novos da BVBA para a Nuvemshop **como
rascunho** e publica todos de uma vez no horario do lancamento.

A regra central: **subir nunca publica**. O upload sempre grava
`published: false`, e a visibilidade so muda por um comando separado e
explicito. Isso e travado em codigo e coberto por teste — nao depende de
ninguem lembrar de desmarcar uma caixinha.

Sem dependencia nenhuma: Python 3.9+ e biblioteca padrao.

---

## O caminho do drop, em 4 comandos

```bash
# 1. Confere a planilha sem tocar na loja
python -m agente_drop validar

# 2. Confere as credenciais
python -m agente_drop conferir

# 3. Sobe tudo como rascunho (invisivel na loja)
python -m agente_drop subir --aplicar

# 4. Agenda a publicacao para as 20h
python -m agente_drop publicar --as 20:00
```

Deu ruim depois de publicar? `python -m agente_drop despublicar --sim` tira
tudo do ar.

---

## Instalacao

```bash
git clone <este-repo> && cd bvba-qa
cp .env.exemplo .env
```

Preencha o `.env`:

```ini
NUVEMSHOP_STORE_ID=1234567
NUVEMSHOP_ACCESS_TOKEN=seu_token_permanente
NUVEMSHOP_USER_AGENT=BVBA Drop Agent (contato@bvba.com.br)
```

O `NUVEMSHOP_USER_AGENT` **precisa** ter um email entre parenteses: a API da
Nuvemshop devolve `400` para requisicao sem User-Agent identificavel. O token
sai do painel em *Meus aplicativos*, na autorizacao do app, e nao expira.

Confirme com `python -m agente_drop conferir` — ele imprime o nome da loja se
tudo estiver certo, e diz exatamente o que corrigir se nao estiver.

---

## Preenchendo o catalogo

Os produtos ficam em `catalogo/produtos.csv`. Uma linha por variante; linhas
com o mesmo `nome` viram um produto com varios tamanhos.

```csv
nome,descricao,sku,preco,estoque,tamanho,peso,imagens
Camiseta Signature,"Malha 240g.",BVBA-CAM-P,199.90,12,P,0.35,https://.../1.jpg
Camiseta Signature,,BVBA-CAM-M,199.90,25,M,0.38,
Camiseta Signature,,BVBA-CAM-G,199.90,25,G,0.41,
```

Os cabecalhos aceitam acento e ingles (`Preço`, `price`, `valor` — tudo cai no
mesmo lugar). A lista completa esta em [`catalogo/COLUNAS.md`](catalogo/COLUNAS.md),
e ha um exemplo preenchido em `catalogo/exemplo-drop.csv`.

Tambem aceita JSON (`--catalogo produtos.json`), com variantes aninhadas.

### Validar antes de subir

```bash
python -m agente_drop validar
```

Aponta com numero de linha o que a Nuvemshop rejeitaria ou o que sairia torto:
preco faltando, promocional maior que o cheio, SKU repetido, foto que nao
existe no disco, variante sem tamanho, mais de 3 atributos. **Erro** bloqueia
o upload; **aviso** so informa.

---

## Subindo

Duas formas.

**Pelo GitHub, sem token na sua maquina** (aba *Actions* > *Subir drop
(rascunho)* > *Run workflow*). O token fica so nos secrets do repositorio,
ninguem precisa colar credencial em lugar nenhum. Deixe `simular` marcado na
primeira vez para ver o plano; desmarque para subir de verdade. Ao final o
workflow comita o `.estado_drop.json`, que e o que a publicacao das 20h usa.

**Ou pelo terminal:**

```bash
python -m agente_drop plano          # mostra o que faria, sem escrever
python -m agente_drop subir --aplicar
```

Sem `--aplicar` o comando so simula. O que o agente faz:

- cria cada produto com todas as variantes, ja com preco, estoque, peso, SKU e
  codigo de barras;
- gera slug, `seo_title` e `seo_description` a partir do nome, da marca e da
  descricao, quando voce nao preencheu;
- envia as fotos **uma requisicao por foto**, para que uma imagem quebrada nao
  derrube o produto inteiro;
- respeita o limite da API (balde de 40 requisicoes, 2 por segundo) e tenta de
  novo sozinho em `429` e `5xx`, com backoff;
- grava tudo em `.estado_drop.json` a cada produto.

### Pode rodar de novo, sem medo

O `.estado_drop.json` liga cada SKU ao ID criado na loja. Rodar de novo:

- produto novo na planilha → cria;
- produto que mudou → atualiza (so as variantes que mudaram; fotos ja enviadas
  nao sobem duas vezes);
- produto identico → pula.

Nada duplica. E se a loja ja estiver publicada quando voce corrigir uma
descricao, a atualizacao **nao** devolve o produto para rascunho.

---

## Publicando as 20h

Tres formas, da mais autonoma para a mais manual.

### 1. GitHub Actions (ninguem precisa estar no computador)

E o modo recomendado, e o que esta configurado em
`.github/workflows/publicar-drop.yml`.

Configure uma vez, em *Settings > Secrets and variables > Actions*:

| Tipo     | Nome | Valor |
|----------|------|-------|
| Secret   | `NUVEMSHOP_STORE_ID` | o id da loja |
| Secret   | `NUVEMSHOP_ACCESS_TOKEN` | o token |
| Secret   | `NUVEMSHOP_USER_AGENT` | `BVBA Drop Agent (contato@bvba.com.br)` |
| Variable | `DROP_DATA` | a data do drop, `AAAA-MM-DD` |

O `.estado_drop.json` precisa estar comitado — e por ele que o workflow sabe
quais produtos publicar. O workflow *Subir drop* ja faz esse commit sozinho.

O agendamento tem duas protecoes que importam num lancamento:

- o cron dispara as 19:40 de Brasilia e o **agente espera ate 20:00:00 em
  ponto**, porque o cron da GitHub Actions costuma atrasar alguns minutos;
- se mesmo assim o runner so acordar depois das 20h, ele publica na hora —
  desde que o atraso esteja dentro de `--tolerancia` (120 min por padrao).
  Atraso maior que isso, ele **nao** publica sozinho e avisa.

Da para disparar na mao a qualquer momento pela aba *Actions* (inclusive em
modo `simular`, que so mostra o status).

### 2. Deixando um terminal aberto

```bash
python -m agente_drop publicar --as 20:00
```

Espera ate o horario e publica, avisando quanto falta. `Ctrl+C` cancela sem
publicar nada. Aceita `20:00`, `20h`, `20h30` ou `"2026-08-10 20:00"`.

### 3. Na hora, no grito

```bash
python -m agente_drop publicar --agora
```

### Conferindo e revertendo

```bash
python -m agente_drop status          # compara o estado local com a loja
python -m agente_drop despublicar --sim
```

---

## Ensaiando sem tocar na loja real

Da para rodar o drop inteiro contra uma Nuvemshop de mentira, local:

```bash
# terminal 1
python ferramentas/loja_falsa.py

# terminal 2
NUVEMSHOP_API_BASE=http://localhost:8799 \
NUVEMSHOP_STORE_ID=123456 \
NUVEMSHOP_ACCESS_TOKEN=ensaio \
NUVEMSHOP_USER_AGENT="Ensaio (qa@bvba.com.br)" \
python -m agente_drop subir --catalogo catalogo/exemplo-drop.csv \
  --estado /tmp/ensaio.json --aplicar
```

A loja falsa imprime cada produto, variante e foto que recebe — e reproduz as
duas recusas classicas da API real (falta de `Authentication` e User-Agent sem
email), entao serve para testar o tratamento de erro tambem.

---

## Testes

```bash
python -m unittest discover -s testes -t .
```

130 testes, sem rede. Cobrem o parsing de preco brasileiro, o agrupamento de
variantes, as regras de validacao, o rate limit e o retry, a idempotencia, e o
caminho completo da CLI contra um servidor HTTP de verdade.

Dois deles guardam as invariantes que sustentam o drop:

- `test_payload_sempre_sai_como_rascunho` — upload nunca publica;
- `test_update_nao_mexe_na_visibilidade` — corrigir um preco com a loja no ar
  nao derruba o produto.

---

## Estrutura

```
agente_drop/
  catalogo.py    le CSV/JSON, agrupa variantes, entende preco brasileiro
  validacao.py   regras que rodam antes de qualquer chamada de rede
  payload.py     monta o JSON da API (e trava published=false)
  nuvemshop.py   cliente HTTP: auth, rate limit, retry, paginacao
  estado.py      liga SKU -> id do produto; e o que torna tudo idempotente
  agente.py      decide criar/atualizar/pular e executa
  relogio.py     horario de Brasilia e a espera ate o lancamento
  relatorio.py   relatorio em Markdown e JSON
  cli.py         os comandos
catalogo/        a planilha do drop + dicionario de colunas
ferramentas/     loja falsa para ensaio local
testes/          130 testes
```

---

## Detalhes da API que valem saber

Estao tratados no codigo, mas explicam decisoes que parecem estranhas:

- o header de autenticacao da v1 se chama `Authentication`, **nao**
  `Authorization` (o nome errado devolve 401). As versoes datadas usam
  `Authorization`. O agente manda os dois;
- `User-Agent` e obrigatorio e precisa ter email de contato, ou a resposta e 400;
- o limite e um *leaky bucket*: balde de 40 requisicoes vazando 2 por segundo.
  Estourar devolve 429 com `X-Rate-Limit-Reset` em milissegundos, que o agente
  respeita;
- `name`, `description` e `handle` sao objetos por idioma (`{"pt": "..."}`);
- precos vao como string (`"199.90"`), com ponto decimal.
