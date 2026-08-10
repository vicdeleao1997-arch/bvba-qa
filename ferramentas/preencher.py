"""Aplica preco, estoque e fotos ao catalogo a partir de um arquivo simples.

Existe porque editar 55 linhas de CSV na mao, na correria do drop, e onde o
erro acontece. Aqui e uma linha por peca:

    MLT-001 | 399,90 | 10,15,15,10,5 | 1-8

    python3 ferramentas/preencher.py

Le catalogo/pendencias.txt, escreve catalogo/produtos.csv. Rodar de novo com o
mesmo arquivo da o mesmo resultado -- campo em branco nao apaga o que ja estava.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

TAMANHOS = ["P", "M", "G", "GG", "XGG"]
PADRAO_FOTO = "imagens/BVBA_-{n}.jpg"


class ErroPendencias(Exception):
    """Linha do arquivo de pendencias que nao da para interpretar."""


def parse_preco(texto: str) -> str:
    """'R$ 1.299,90' -> '1299.90'. Vazio devolve ''."""
    texto = (texto or "").strip()
    if not texto:
        return ""
    limpo = re.sub(r"[^\d,.\-]", "", texto)
    if not limpo:
        raise ErroPendencias(f'preco nao numerico: "{texto}"')
    if "." in limpo and "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif "," in limpo:
        limpo = limpo.replace(",", ".")
    try:
        valor = float(limpo)
    except ValueError:
        raise ErroPendencias(f'preco nao numerico: "{texto}"') from None
    if valor <= 0:
        raise ErroPendencias(f"preco precisa ser maior que zero: {texto}")
    return f"{valor:.2f}"


def parse_estoque(texto: str) -> list[str]:
    """'10,15,15,10,5' -> por tamanho. '12' -> 12 em todos. '' -> vazio."""
    texto = (texto or "").strip()
    if not texto:
        return [""] * len(TAMANHOS)

    partes = [p.strip() for p in texto.split(",") if p.strip()]
    for parte in partes:
        if not re.fullmatch(r"\d+", parte):
            raise ErroPendencias(f'estoque nao numerico: "{parte}"')

    if len(partes) == 1:
        return [partes[0]] * len(TAMANHOS)
    if len(partes) == len(TAMANHOS):
        return partes
    raise ErroPendencias(
        f"estoque tem {len(partes)} valor(es); precisa de 1 ou "
        f"{len(TAMANHOS)} (ordem {', '.join(TAMANHOS)})"
    )


def parse_fotos(texto: str) -> list[int]:
    """'1-6, 10, 14' -> [1,2,3,4,5,6,10,14], sem repetir e na ordem escrita."""
    texto = (texto or "").strip()
    if not texto:
        return []

    numeros: list[int] = []
    for bruto in texto.split(","):
        bruto = bruto.strip()
        if not bruto:
            continue
        faixa = re.fullmatch(r"(\d+)\s*-\s*(\d+)", bruto)
        if faixa:
            inicio, fim = int(faixa.group(1)), int(faixa.group(2))
            if fim < inicio:
                raise ErroPendencias(f"faixa invertida: {bruto}")
            if fim - inicio > 200:
                raise ErroPendencias(f"faixa grande demais: {bruto}")
            numeros.extend(range(inicio, fim + 1))
        elif re.fullmatch(r"\d+", bruto):
            numeros.append(int(bruto))
        else:
            raise ErroPendencias(f'nao entendi "{bruto}" na lista de fotos')

    vistos: set[int] = set()
    unicos = []
    for n in numeros:
        if n not in vistos:
            vistos.add(n)
            unicos.append(n)
    return unicos


def ler_pendencias(caminho: Path) -> dict[str, dict]:
    if not caminho.exists():
        raise ErroPendencias(f"nao encontrei {caminho}")

    pendencias: dict[str, dict] = {}
    for numero, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        limpa = linha.strip()
        if not limpa or limpa.startswith("#"):
            continue
        campos = [c.strip() for c in limpa.split("|")]
        if len(campos) < 2:
            raise ErroPendencias(f"linha {numero}: esperava campos separados por |")

        ref = campos[0]
        if not ref:
            continue
        campos += [""] * (4 - len(campos))

        try:
            pendencias[ref] = {
                "preco": parse_preco(campos[1]),
                "estoque": parse_estoque(campos[2]),
                "fotos": parse_fotos(campos[3]),
            }
        except ErroPendencias as erro:
            raise ErroPendencias(f"linha {numero} ({ref}): {erro}") from None

    return pendencias


def aplicar(
    catalogo: Path, pendencias: dict[str, dict], pasta_imagens: Path
) -> tuple[int, list[str]]:
    with catalogo.open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        colunas = list(leitor.fieldnames or [])
        linhas = [dict(l) for l in leitor]

    for obrigatoria in ("grupo", "sku", "preco", "estoque", "tamanho", "imagens"):
        if obrigatoria not in colunas:
            raise ErroPendencias(f"o catalogo nao tem a coluna '{obrigatoria}'")

    alterados = 0
    avisos: list[str] = []
    refs_no_catalogo = {l["grupo"] for l in linhas}

    for ref in pendencias:
        if ref not in refs_no_catalogo:
            avisos.append(f'{ref}: nao existe no catalogo, ignorado')

    ja_recebeu_foto: set[str] = set()

    for linha in linhas:
        ref = linha["grupo"]
        dados = pendencias.get(ref)
        if not dados:
            continue

        mudou = False

        if dados["preco"]:
            if linha.get("preco") != dados["preco"]:
                linha["preco"] = dados["preco"]
                mudou = True

        tamanho = linha.get("tamanho", "")
        if tamanho in TAMANHOS:
            valor = dados["estoque"][TAMANHOS.index(tamanho)]
            if valor and linha.get("estoque") != valor:
                linha["estoque"] = valor
                mudou = True

        # As fotos ficam so na primeira linha do grupo: sao do produto,
        # nao da variante.
        if dados["fotos"] and ref not in ja_recebeu_foto:
            arquivos = [PADRAO_FOTO.format(n=n) for n in dados["fotos"]]
            faltando = [a for a in arquivos if not (pasta_imagens.parent / a).exists()]
            if faltando:
                avisos.append(
                    f"{ref}: {len(faltando)} foto(s) ainda nao estao no disco "
                    f"(ex.: {faltando[0]})"
                )
            novo = "|".join(arquivos)
            if linha.get("imagens") != novo:
                linha["imagens"] = novo
                mudou = True
            ja_recebeu_foto.add(ref)

        if mudou:
            alterados += 1

    with catalogo.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)

    return alterados, avisos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pendencias", default="catalogo/pendencias.txt")
    parser.add_argument("--catalogo", default="catalogo/produtos.csv")
    parser.add_argument("--imagens", default="imagens")
    args = parser.parse_args(argv)

    try:
        pendencias = ler_pendencias(Path(args.pendencias))
        alterados, avisos = aplicar(
            Path(args.catalogo), pendencias, Path(args.imagens)
        )
    except ErroPendencias as erro:
        print(f"Erro: {erro}")
        return 2

    preenchidas = sum(1 for d in pendencias.values() if d["preco"])
    com_foto = sum(1 for d in pendencias.values() if d["fotos"])

    print(f"{alterados} linha(s) do catalogo atualizada(s).")
    print(f"  preco preenchido em {preenchidas}/{len(pendencias)} peca(s)")
    print(f"  fotos mapeadas em {com_foto}/{len(pendencias)} peca(s)")

    for aviso in avisos:
        print(f"  ! {aviso}")

    print()
    print("Confira com: python3 -m agente_drop validar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
