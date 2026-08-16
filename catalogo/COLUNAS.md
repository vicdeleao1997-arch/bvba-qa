# Dicionario de colunas do catalogo

Uma linha = uma variante. Linhas com o **mesmo nome** viram um produto so, com
varias variantes. Ou seja, uma camiseta em P/M/G/GG ocupa 4 linhas com o mesmo
`nome` e `tamanho` diferente.

Os cabecalhos aceitam acento, maiuscula e espaco (`Preço Promocional` funciona
igual a `preco_promocional`), e tambem os nomes em ingles.

## Obrigatorias

| Coluna  | Apelidos aceitos            | Exemplo    | Observacao |
|---------|-----------------------------|------------|------------|
| `nome`  | name, produto, titulo       | Camiseta Oversized | Repita igual em todas as linhas da mesma peca |
| `preco` | price, valor, preco_venda   | 199,90     | Aceita `R$ 1.299,90`, `1299.90` ou `199,90` |

## Fortemente recomendadas

| Coluna    | Apelidos              | Exemplo | Por que importa |
|-----------|-----------------------|---------|-----------------|
| `sku`     | codigo, code          | BVBA-CAM-SIG-M | Sem SKU o agente nao reconhece a variante numa segunda execucao e pode duplicar |
| `estoque` | stock, quantidade, qtd| 25      | Em branco = venda sem controle de estoque. `0` = entra esgotada |
| `peso`    | weight, peso_kg       | 0,35    | Em kg. Sem peso o frete pode falhar no checkout |
| `imagens` | fotos, images         | ver abaixo | Produto sem foto vai pro ar como placeholder cinza |

## Variacoes

| Coluna     | Apelidos      | Exemplo |
|------------|---------------|---------|
| `tamanho`  | size, talle   | M |
| `cor`      | color, colour | Preto |
| `atributo_*` | attr_*, opcao_* | `atributo_estampa` -> vira a opcao "Estampa" |

Maximo de **3 atributos por produto** (limite da Nuvemshop). Todas as linhas do
mesmo produto precisam preencher as mesmas colunas de atributo — se uma linha
tem `tamanho` e outra nao, o agente acusa erro antes de subir.

## Opcionais

| Coluna | Apelidos | Exemplo |
|--------|----------|---------|
| `descricao` | description, detalhes | Malha pesada 240g. Aceita HTML |
| `preco_promocional` | promotional_price, promo | 149,90 (precisa ser menor que `preco`) |
| `custo` | cost | 80,00 (nao aparece na loja) |
| `marca` | brand | BVBA |
| `categorias` | categoria, colecao | `Camisetas\|Drop 01` |
| `tags` | etiquetas | `drop01\|oversized` |
| `codigo_barras` | barcode, ean, gtin | 7891234567890 |
| `largura`, `altura`, `profundidade` | width, height, depth | em cm |
| `handle` | slug, url | camiseta-oversized-signature (gerado do nome se vazio) |
| `seo_titulo` | seo_title | gerado do nome + marca se vazio |
| `seo_descricao` | seo_description | gerado da descricao se vazio |
| `frete_gratis` | free_shipping | sim / nao |
| `video` | video_url, youtube | link do YouTube |
| `grupo` | ref, referencia | use quando dois produtos tem o mesmo nome |

## Imagens

Separe varias com `|`. Duas formas, misturaveis na mesma celula:

- **URL**: `https://cdn.exemplo.com/foto1.jpg|https://cdn.exemplo.com/foto2.jpg`
- **Arquivo local**: `imagens/cargo-frente.png|imagens/cargo-costas.png`
  (caminho relativo a pasta passada em `--imagens`, que por padrao e a raiz do
  projeto)

A primeira imagem da lista vira a foto de capa. As fotos ficam apenas no
produto da primeira linha do grupo — nao precisa repetir em cada tamanho.

## O que **nao** existe

Nao ha coluna de publicacao. Isso e proposital: o upload sempre cria o produto
como rascunho, e a visibilidade so muda pelo comando `publicar`.
