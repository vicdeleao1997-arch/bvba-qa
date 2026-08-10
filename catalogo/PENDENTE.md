# O que falta para o DROP 2 subir

O catálogo `produtos.csv` já tem as **11 peças da coleção AW 2026**, 5 tamanhos
cada (P/M/G/GG/XGG) = **55 variantes**, com nome, cor, SKU, descrição e
categoria — tudo extraído da ficha técnica do Drive.

Fonte: **`Fichas Técnicas Adriano 27.06.26.pdf`** (a mais recente das duas
versões no Drive; a outra é `Fichas Técnicas 02.06.26.pdf`, "DROP 2 ARTS").

Rodar `python -m agente_drop validar` hoje devolve **55 erros de preço** — de
propósito. O agente se recusa a subir peça sem preço.

## As 11 peças

| REF | Peça | Cor | SKUs |
|---|---|---|---|
| MLT-001 | Moletom Canguru Oversized | Marrom Café | BVBA-MLT-001-{P..XGG} |
| CJW-002 | Calça Jeans Oversized Wide Conversível | Preto | BVBA-CJW-002-{P..XGG} |
| JRT-003 | Jorts Jeans Oversized Wide | Preto | BVBA-JRT-003-{P..XGG} |
| CMS-004 | Camiseta Oversized Boxy | Off White | BVBA-CMS-004-{P..XGG} |
| CMS-005 | Camiseta Oversized Boxy | Azul Escuro | BVBA-CMS-005-{P..XGG} |
| CMS-006 | Camiseta Oversized Boxy | Azul Escuro | BVBA-CMS-006-{P..XGG} |
| CMS-007 | Camiseta Oversized Boxy | Marrom Claro | BVBA-CMS-007-{P..XGG} |
| CMS-008 | Camiseta Oversized Boxy | Cinza Chumbo | BVBA-CMS-008-{P..XGG} |
| CMS-009 | Camiseta Oversized Boxy (peito esquerdo) | Azul Escuro | BVBA-CMS-009-{P..XGG} |
| CMS-010 | Camiseta Oversized Boxy (peito esquerdo) | Marrom Café | BVBA-CMS-010-{P..XGG} |
| CMS-011 | Camiseta Oversized Boxy (peito esquerdo) | Cinza Chumbo | BVBA-CMS-011-{P..XGG} |

## 1. Preços — bloqueia o drop

Nenhuma das duas fichas técnicas traz preço. Preencher a coluna `preco`
(e `preco_promocional`, se houver). Aceita `199,90` ou `R$ 199,90`.

Basta um preço por peça — dá para repetir nas 5 linhas do mesmo REF.

## 2. Estoque por tamanho — bloqueia a venda, não o upload

Coluna `estoque`. Em branco = venda sem controle de estoque (a peça nunca
esgota sozinha). `0` = entra esgotada.

## 3. Fotos — o mapeamento não existe

As fotos de fundo branco estão em **`FUNDO BRANCO — FINAL (97 fotos)`**, mas os
arquivos se chamam `BVBA_-1.jpg`, `BVBA_-2.jpg` … `BVBA_-125.jpg`. **O nome do
arquivo não diz qual peça é.** Sem isso não dá para montar a coluna `imagens`
sem chutar.

O que resolve, em ordem de esforço:

- dizer as faixas: "1 a 12 = MLT-001, 13 a 20 = CJW-002, …"; ou
- renomear os arquivos no Drive para o REF (`CMS-004_01.jpg`); ou
- criar uma subpasta por REF.

Atenção também: **link do Drive não funciona como origem de imagem na
Nuvemshop.** Os arquivos são privados, e a API precisa de uma URL pública ou do
arquivo em si. Dois caminhos: tornar a pasta pública e usar os links diretos, ou
baixar as fotos para `imagens/` no repositório e referenciar o caminho local —
o agente envia o arquivo em base64 nesse caso.

## 4. Nomes comerciais — confirmar

Na ficha, 8 das 11 peças se chamam literalmente "CAMISETA OVERSIZED BOXY". Três
pares têm nome e cor idênticos, diferindo só pela estampa. Os nomes no
`produtos.csv` são **provisórios**, montados a partir de cor e posição da
estampa, para que cada página fique distinguível na loja. Se a coleção tem nomes
de verdade, é melhor trocar antes de subir.

## 5. Divergência entre as duas fichas

O **CMS-007** aparece como **Marrom Claro** na ficha de 27.06 e como **Marrom
Café** na de 02.06. O catálogo seguiu a mais recente (Marrom Claro). Vale
confirmar.

O MLT-001 também mudou: a ficha de 02.06 diz "estampa nas costas abaixo do
capuz"; a de 27.06 diz "estampa deslocada à direita nas costas, 15 cm". A
descrição seguiu a mais recente.

## 6. Dados que a ficha não preenche

Composição, gramatura, lavagem e a tabela de medidas estão todos como `-` no
PDF. Nada disso bloqueia o upload, mas medidas ajudam muito na conversão —
vale preencher a coluna `peso` pelo menos (o frete depende dela).
