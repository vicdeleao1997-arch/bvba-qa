# DROP 2 — o que falta

O catálogo `produtos.csv` já tem as **11 peças da coleção AW 2026**, 5 tamanhos
cada (P/M/G/GG/XGG) = **55 variantes**.

Fonte: **`Fichas Técnicas Adriano 27.06.26.pdf`** (a mais recente das duas
versões no Drive; a outra é `Fichas Técnicas 02.06.26.pdf`, "DROP 2 ARTS").

## Já preenchido

- nome, cor, SKU (derivado do REF de produção), descrição escrita a partir das
  especificações da ficha, categoria e tags
- **peso — estimado**, ver a ressalva abaixo
- SEO: o agente gera `seo_title` e `seo_description` do nome, marca e descrição

## Falta você

Uma linha por peça em **`catalogo/pendencias.txt`**, depois um comando:

```bash
python3 ferramentas/preencher.py
python3 -m agente_drop validar
```

Exemplo de linha preenchida:

```
MLT-001   | 449,90 | 8,12,12,8,4 | 1-8
```

- **preço** — obrigatório. Sem ele o agente se recusa a subir a peça.
  Aceita `449,90`, `R$ 449,90` ou `449.90`.
- **estoque** — um número por tamanho na ordem P,M,G,GG,XGG, ou um número só
  para todos. Vazio = vende sem controle de estoque.
- **fotos** — os números dos arquivos `BVBA_-N.jpg`, em faixas (`1-8`) ou soltos
  (`1-6, 10, 14`). A primeira vira a capa.

Campo em branco não apaga o que já estava, e rodar duas vezes dá o mesmo
resultado.

## As 11 peças

| REF | Peça | Cor |
|---|---|---|
| MLT-001 | Moletom Canguru Oversized | Marrom Café |
| CJW-002 | Calça Jeans Oversized Wide Conversível | Preto |
| JRT-003 | Jorts Jeans Oversized Wide | Preto |
| CMS-004 | Camiseta Oversized Boxy | Off White |
| CMS-005 | Camiseta Oversized Boxy | Azul Escuro |
| CMS-006 | Camiseta Oversized Boxy | Azul Escuro |
| CMS-007 | Camiseta Oversized Boxy | Marrom Claro |
| CMS-008 | Camiseta Oversized Boxy | Cinza Chumbo |
| CMS-009 | Camiseta Oversized Boxy (peito esquerdo) | Azul Escuro |
| CMS-010 | Camiseta Oversized Boxy (peito esquerdo) | Marrom Café |
| CMS-011 | Camiseta Oversized Boxy (peito esquerdo) | Cinza Chumbo |

## Ressalvas — vale 30 segundos de conferência

**Peso é estimativa minha, não da ficha.** A ficha traz gramatura e medidas como
`-`. Usei valores de mercado para as modelagens descritas: camiseta 0,30–0,44 kg,
moletom 0,75–1,00 kg, calça 0,80–1,02 kg, jorts 0,50–0,66 kg, variando por
tamanho. **O frete é cobrado em cima disso** — se estiver longe do real, a BVBA
paga a diferença em cada pedido. Vale pesar uma peça de cada tipo.

**Os nomes das camisetas são provisórios.** Na ficha, 8 das 11 peças se chamam
literalmente "CAMISETA OVERSIZED BOXY", e três pares têm nome e cor idênticos.
Montei nomes a partir de cor e posição da estampa só para as páginas ficarem
distinguíveis. Se a coleção tem nomes de verdade, troque a coluna `nome` antes
de subir.

**CMS-007 diverge entre as fichas**: Marrom Claro na de 27.06, Marrom Café na de
02.06. Segui a mais recente. O MLT-001 também mudou de estampa nas costas entre
as duas versões; a descrição segue a de 27.06.

**As fotos precisam estar no disco.** Link do Drive não funciona como origem de
imagem na Nuvemshop — os arquivos são privados. Baixe a pasta
`FUNDO BRANCO — FINAL (97 fotos)` para `imagens/` no repositório mantendo os
nomes `BVBA_-N.jpg`; o agente envia cada arquivo em base64. O validador avisa se
alguma foto referenciada não estiver lá.

## Depois de preencher

```bash
python3 ferramentas/preencher.py       # aplica pendencias.txt no catalogo
python3 -m agente_drop validar         # confere tudo, sem tocar na loja
python3 -m agente_drop subir --aplicar # cria as 11 páginas como RASCUNHO
python3 -m agente_drop publicar --as 20:00
```

Ou, se preferir não ter o token na máquina: cadastre os secrets no repositório e
use os workflows *Subir drop (rascunho)* e *Publicar drop* na aba Actions.
