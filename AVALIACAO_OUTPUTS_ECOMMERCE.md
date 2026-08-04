# Avaliação — outputs de imagem BVBA para o e-commerce da nova coleção

**Data:** 2026-08-04 · **Escopo:** histórico de geração Magnific + golden sets aprovados no Drive

---

## 0. Limitação importante desta avaliação (ler primeiro)

**Não consegui inspecionar os pixels.** O ambiente em que rodei bloqueia por política de rede
todos os hosts onde as imagens vivem (`pikaso.cdnpk.net`, `drive.google.com`,
`googleusercontent.com`, `fal.media`, `magnific.com` — todos respondem 403 no proxy), e as rotas
alternativas que tentei também não passaram:

| Rota tentada | Resultado |
|---|---|
| `curl` direto nos renders / thumbnails | 403 no proxy (política de rede) |
| Download via Google Drive (`download_file_content`) | arquivos de 17–22 MB, inviável trazer inteiros |
| Leitura de imagem via Drive (`read_file_content` em PNG) | retorna vazio — não faz visão nesses arquivos |
| Baixar + reduzir num sandbox remoto com internet | ferramenta exigiu aprovação; sessão não-interativa |

Ou seja: **isto é uma avaliação do registro de produção, não um QA visual.** Tudo abaixo é
verificável nos metadados (prompts, datas, modelo, resolução, custo, contagens) e nos `RECIPE.md`
que vocês mesmos escreveram. Onde a conclusão dependeria de olhar a imagem, eu digo isso
explicitamente em vez de chutar. A seção 6 diz exatamente o que destravar para eu fechar o QA visual.

---

## 1. O que são os outputs da nova coleção

O trabalho corrente **não é geração de modelo sintético** — é **substituição de fundo em foto real**.

A foto-fonte está no histórico como upload: *"19-year-old white female with long blonde hair
wearing a brown hoodie with 'BVBA' in yellow text and black cargo shorts, standing in front of a
textured wall"*. Ou seja: moletom BVBA marrom + cargo shorts preto — a coleção nova, fotografada
de verdade, numa sala de parede texturizada que jogou dominante quente na cena.

O brief de produção (prompt, `imagen-nano-banana-2`, 4K, 832×1216) pede:

1. neutralizar a dominante quente da sala → branco realmente branco;
2. **congelar o enquadramento** (mesma posição, mesmo tamanho, mesmo crop);
3. **congelar a pessoa e a roupa** — só pixels não cobertos pela pessoa podem mudar;
4. ciclorama branco infinito, sem borda/rolo/tripé/canto visível;
5. superfície limpa, luz coerente com a luz que já está na pessoa;
6. sombra de contato real nos pés;
7. recorte sem halo claro nem escuro, cabelo com fios translúcidos preservados.

O brief está **tecnicamente muito bem escrito** — é praticamente a checklist canônica de composição
de moda, com critérios de falha declarados ("if the framing differs from the source, the result is a
failed generation"). Não é aí que está o problema.

## 2. Volume e cadência — o sinal mais forte que consigo medir

| Janela | Gerações |
|---|---|
| desde 18/jul | 216 |
| desde 01/ago | 132 |
| desde 03/ago | 111 |
| **04/ago, 00:00–01:06 UTC** | **88** |

**88 gerações em 66 minutos**, na madrugada, no mesmo brief. A 150 créditos por render 4K
(custo confirmado no último item), isso é da ordem de **13 mil créditos numa única sessão** —
e ~20 mil desde 1º de agosto, se a média se mantiver.

Esse padrão tem uma leitura só: **re-roll em massa tentando acertar por sorteio uma tarefa que é
determinística.** E isso contradiz frontalmente a doutrina que vocês mesmos fixaram no
`RECIPE.md` do golden set da camiseta:

> "REGRA DE RECURSO: nunca re-rolar geração PAGA pra mudar tamanho/forma/posição de estampa —
> é dial de composite local ($0)."

A regra foi escrita para estampa, mas o raciocínio é idêntico aqui. Troca de fundo com
**enquadramento congelado e sujeito congelado** é, por definição, um trabalho de **máscara +
composição**: recorta a pessoa uma vez, gera *um* ciclorama limpo, compõe, harmoniza cor, planta a
sombra de contato, adiciona grão. Iterar custa zero e o resultado é reprodutível. Pedir isso à IA
generativa a cada tentativa é pagar 150 créditos por um sorteio em que os itens 2 e 3 do próprio
brief (não mudar o enquadramento, não mudar a roupa) são justamente os que o modelo mais tende a
violar.

**Esta é a principal recomendação do relatório** e está detalhada na seção 5.

## 3. Padrão histórico: o mesmo ciclo já aconteceu na campanha do gorro

Não é um caso isolado — é a segunda vez que o mesmo ciclo se repete, e a primeira vez foi resolvida
corretamente. Vale registrar porque a lição já está paga.

Nas **289 gerações com "BVBA" no prompt** (campanha gorro TCA-001 + camiseta Fuck Negativity), dá
para ler a briga defeito a defeito, porque cada re-roll incorporou o defeito anterior na lista de
`avoid:`. A taxonomia que emerge:

| Defeito | Como aparece na evolução dos prompts |
|---|---|
| **Punho/dobra no gorro** | o mais teimoso. Vira `NO CUFF`, depois `NO CUFF and NO FOLD`, depois `NO turned-up band, NO rolled edge, NO double-layer, NO horizontal fold line`, depois um edit dedicado só para remover a dobra |
| **Posição das etiquetas** | patch oval e tag do gato migram para o centro / para o mesmo lado / para cima. Prompts passam a especificar "lados OPOSTOS, ambos BAIXO, bem separados" |
| **Patch ilegível** | vira um edit específico só para aumentar e dar nitidez ao patch |
| **Silhueta errada** | "short skull-cap" vs. "TALL crown ending in a soft point" — dois modelos mentais do produto brigando entre re-rolls |
| **Deriva de identidade** | de "the SAME woman" para "COMBINE the FIRST FOUR references", "unmistakably HER, not a look-alike" |
| **Expressão** | oscila entre `warm genuine HAPPY smile` e `calm NEUTRAL, not smiling` — direção de arte mudando no meio da campanha |

Empilhar negativos é sintoma, não cura: cada `avoid:` novo é a confissão de que a tentativa anterior
saiu errada, e o prompt final do gorro carrega ~15 negativos.

**O importante: vocês saíram desse ciclo pela via certa.** O `RECIPE.md` da camiseta fixa uma
hierarquia de métodos por realismo e um método oficial:

1. geração nativa completa (modelo já vestindo a peça na cena);
2. edit sobre plate — "lê levemente colada", só para delta rápido;
3. composite — fiel mas artificial na malha, só fallback/QA de escala.

…e conclui adotando **displacement composite** (`print_composite2.py`) como método oficial para
estampa com micro-detalhe: *"Fidelidade 100% (arte real, IA nunca toca) + realismo físico"*, com
tamanho parametrizado (`--width-px`, ~0,27 × vão da peça) ajustável de graça.

Isso é maduro: o problema foi tirado da mão da IA e devolvido para um pipeline determinístico.
**A campanha atual de fundo abandonou essa lição.**

## 4. Estado documental dos aprovados (o que já está fechado)

O golden set no Drive (`BVBA_FAL_AI_APROVADOS`, compilado 11/jul) está bem organizado — cada pasta
com `RECIPE.md` reproduzível:

| Pasta | Peça | Aprovados | Data |
|---|---|---|---|
| `03_gorro_eric_maria` | gorro TCA-001 | Eric e Maria, frente + diagonal (4) + `REF_flat` + `REF_identity` | 07/jul |
| `02_gorro_yumi_kaio` | gorro | Yumi e Kaio, frente (2) + refs de identidade | — |
| `01_FN_yumi_kaio_estampa` | camiseta Fuck Negativity | Yumi (nativa + definitiva), Kaio (displacement) + plates limpos reutilizáveis | 10–11/jul |

Pontos fortes reais desse conjunto:

- **rastreabilidade**: cada aprovado registra os laços usados e em que ordem;
- **protocolo de regressão declarado** — regenerar `eric_frente` e `maria_diagonal` com os mesmos
  laços e comparar pareado; piorou em qualquer critério, não adota;
- **plates limpos guardados** para as próximas poses/peças (delta-only), evitando regeração completa;
- **truque cross-model documentado**: `eric_master` usado como *shape authority* na geração da Maria;
- **diretiva de pose** ("sempre humanizadas/naturais — nunca repetir frontal estático").

Duas lacunas documentais:

- a rubrica de QA (`QA_RUBRICA_FIDELIDADE.md`) é citada como obrigatória em ambos os `RECIPE.md`,
  mas **não está no Drive junto com o golden set** — ela vive só na máquina local
  (`~/BVBA_AI_CEO/00_brand/`). O gate de aprovação não é auditável por ninguém além de quem tem a
  máquina;
- **não existe registro de aprovação para a leva atual de troca de fundo.** As 132 gerações desde
  1º/ago não têm `RECIPE.md`, não têm pasta de aprovados, não têm nota de QA. Do ponto de vista do
  histórico, essa leva é 132 tentativas sem um vencedor declarado.

## 5. Riscos concretos para o e-commerce

Ordenados por impacto. Os marcados 🔍 dependem de olhar as imagens para confirmar — o brief
os prevê como modo de falha, o que significa que já apareceram.

1. **Custo e cadência insustentáveis (confirmado).** 88 renders/hora em brief determinístico.
   Não escala para um catálogo inteiro.
2. **Ausência de gate de aprovação na leva atual (confirmado).** Sem aprovado declarado, o risco
   é subir no PDP uma variante que ninguém bateu o martelo.
3. **Inconsistência de proporção entre levas (confirmado).** A campanha do gorro saiu em 832×1024
   (≈4:5, amigável a marketplace). A leva atual sai em 832×1216 (≈2:3). Catálogo com dois aspectos
   quebra o grid da PDP e pode bater em spec de marketplace (Amazon/Shopee/Mercado Livre pedem
   tipicamente 1:1, 4:5 ou 3:4). **Vale fechar a proporção antes de gerar o resto.**
4. 🔍 **Deriva de enquadramento** — o brief declara isso como falha ("A different composition is a
   failed generation"), então aconteceu. Num carrossel de PDP, escala de produto inconsistente
   entre fotos é imediatamente visível.
5. 🔍 **Alteração da peça** — o item [3] do brief insiste que costuras, formas e a estampa não podem
   ser redesenhadas. Se o modelo "consertou" o moletom, é **fidelidade de produto**: a foto passa a
   mostrar algo que o cliente não vai receber. É o defeito mais caro (devolução, reclamação).
6. 🔍 **Resíduo da dominante quente / halo de recorte / sombra de contato ausente** — os três
   sintomas clássicos de composição, todos explicitamente listados no brief.

## 6. Recomendações

**Imediato — parar de sortear a troca de fundo.** O caminho é o mesmo que já funcionou para a
estampa: tirar a tarefa determinística da mão da IA.

1. **Recorte uma vez, componha muitas.** Matte da pessoa por remoção de fundo dedicada, um
   ciclorama branco gerado uma única vez (ou fotografado), e composição local: harmonização de cor,
   sombra de contato, grão. Iteração vira dial local de custo zero — exatamente o que o
   `PRINT_FIDELITY_PLAYBOOK` já prega.
2. Com o sujeito congelado por construção, os riscos 4, 5 e 6 acima **deixam de existir**: não há
   como o enquadramento mudar ou a roupa ser redesenhada se a IA nunca toca nesses pixels.
3. **Correção de dominante é etapa de cor, não de geração.** Neutralizar a parede quente é balanço
   de branco + máscara, resolvido de forma reprodutível e reversível.

**Processo:**

4. **Fixe a proporção do catálogo agora** (recomendo 4:5, que já é o que o golden set do gorro usa
   e atende à maioria dos marketplaces) e regere/recorte o que estiver fora.
5. **Suba a `QA_RUBRICA_FIDELIDADE.md` para o Drive**, ao lado dos golden sets. Gate de aprovação
   que só existe numa máquina não é gate.
6. **Crie `04_fundo_branco_colecao_nova/` no `BVBA_FAL_AI_APROVADOS`** com `RECIPE.md` e os
   aprovados desta leva — mesmo padrão dos outros três. Hoje as 132 gerações não têm vencedor
   registrado.
7. **Aplique o protocolo de regressão pareado** que vocês já definiram antes de trocar de método.

**Para destravar o QA visual (o que falta para eu fechar esta avaliação):**

- liberar no ambiente o acesso a `pikaso.cdnpk.net` / `drive.google.com`, **ou**
- aprovar a ferramenta de sandbox remoto (baixo o render lá, reduzo e trago), **ou**
- colocar as candidatas desta leva numa pasta do Drive em versão reduzida (≤ 1500 px de lado).

Com qualquer uma das três eu faço o QA imagem a imagem: enquadramento vs. fonte, fidelidade da
peça, recorte/halo, sombra de contato, neutralidade de branco e consistência entre as fotos do
carrossel.

---

## Resumo em uma linha

O **brief está excelente e o golden set do gorro/camiseta está maduro e rastreável** — mas a leva
atual de troca de fundo da coleção nova **abandonou a doutrina que vocês mesmos escreveram**:
132 gerações pagas desde 1º/ago (88 delas em uma hora) sorteando uma tarefa que é composição
determinística, sem aprovado declarado e numa proporção diferente da do resto do catálogo.
Trocar re-roll por matte + composição resolve custo, consistência e os três maiores riscos de
qualidade de uma vez.
