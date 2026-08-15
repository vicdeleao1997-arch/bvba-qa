"""Leitura do catalogo de produtos (CSV ou JSON) e normalizacao.

Uma linha do CSV = uma variante. Linhas com o mesmo produto (mesmo ``grupo``,
ou na falta dele o mesmo ``nome``) viram um produto com varias variantes.
Os nomes de coluna aceitam apelidos em portugues e ingles porque a planilha
raramente chega no formato exato.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

SEPARADORES_LISTA = ("|", ";", ",")


class ErroCatalogo(Exception):
    """Arquivo de catalogo ilegivel ou mal formado."""


# Cada campo interno e a lista de cabecalhos que aceitamos para ele.
APELIDOS: dict[str, tuple[str, ...]] = {
    "grupo": ("grupo", "group", "produto_id", "id_produto", "ref", "referencia"),
    "nome": ("nome", "name", "produto", "product", "titulo", "title"),
    "descricao": ("descricao", "description", "descricao_html", "detalhes"),
    "sku": ("sku", "codigo", "code", "cod"),
    "preco": ("preco", "price", "valor", "preco_venda"),
    "preco_promocional": (
        "preco_promocional",
        "promotional_price",
        "preco_promo",
        "promo",
        "preco_desconto",
    ),
    "custo": ("custo", "cost", "preco_custo"),
    "estoque": ("estoque", "stock", "quantidade", "qtd", "qty", "inventario"),
    "peso": ("peso", "weight", "peso_kg"),
    "largura": ("largura", "width"),
    "altura": ("altura", "height"),
    "profundidade": ("profundidade", "depth", "comprimento", "length"),
    "codigo_barras": ("codigo_barras", "barcode", "ean", "gtin"),
    "tamanho": ("tamanho", "size", "talle"),
    "cor": ("cor", "color", "colour"),
    "marca": ("marca", "brand"),
    "categorias": ("categorias", "categoria", "categories", "category", "colecao"),
    "tags": ("tags", "etiquetas", "palavras_chave"),
    "imagens": ("imagens", "images", "fotos", "photos", "imagem", "foto", "image"),
    "handle": ("handle", "slug", "url"),
    "seo_titulo": ("seo_titulo", "seo_title", "titulo_seo"),
    "seo_descricao": ("seo_descricao", "seo_description", "descricao_seo"),
    "frete_gratis": ("frete_gratis", "free_shipping", "frete_free"),
    "video": ("video", "video_url", "youtube"),
}

# Colunas livres viram atributos de variante: "atributo_estampa", "attr_lavagem".
PREFIXOS_ATRIBUTO = ("atributo_", "attr_", "opcao_", "option_")


def normalizar_chave(texto: str) -> str:
    """'Preço Promocional ' -> 'preco_promocional'."""
    sem_acento = unicodedata.normalize("NFKD", texto or "")
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    sem_acento = sem_acento.strip().lower()
    sem_acento = re.sub(r"[^a-z0-9]+", "_", sem_acento)
    return sem_acento.strip("_")


def _mapa_apelidos() -> dict[str, str]:
    mapa: dict[str, str] = {}
    for campo, apelidos in APELIDOS.items():
        for apelido in apelidos:
            mapa[apelido] = campo
    return mapa


MAPA_APELIDOS = _mapa_apelidos()


def slugificar(texto: str) -> str:
    base = normalizar_chave(texto).replace("_", "-")
    return re.sub(r"-+", "-", base).strip("-")


def parse_decimal(valor: Any) -> str | None:
    """Aceita 'R$ 1.299,90', '1299.90', '1.299,90', 1299.9 -> '1299.90'.

    Regra: se '.' e ',' aparecem juntos, o '.' e separador de milhar e a ','
    e decimal. Sozinhos, ambos sao tratados como separador decimal.
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return f"{float(valor):.2f}"

    texto = str(valor).strip()
    if not texto:
        return None

    texto = re.sub(r"[^\d,.\-]", "", texto)
    if not texto or texto in {"-", ".", ","}:
        return None

    if "." in texto and "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        return f"{float(texto):.2f}"
    except ValueError:
        return None


def parse_inteiro(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    texto = re.sub(r"[^\d\-]", "", str(valor))
    if not texto or texto == "-":
        return None
    try:
        return int(texto)
    except ValueError:
        return None


def parse_bool(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    return str(valor or "").strip().lower() in {
        "1", "sim", "s", "true", "t", "yes", "y", "verdadeiro", "x",
    }


def parse_lista(valor: Any) -> list[str]:
    """Divide 'a|b|c' ou 'a, b' em lista, preservando URLs com virgula rara."""
    if valor is None:
        return []
    if isinstance(valor, (list, tuple)):
        return [str(v).strip() for v in valor if str(v).strip()]

    texto = str(valor).strip()
    if not texto:
        return []
    for sep in SEPARADORES_LISTA:
        if sep in texto:
            return [p.strip() for p in texto.split(sep) if p.strip()]
    return [texto]


@dataclass
class Variante:
    sku: str = ""
    preco: str | None = None
    preco_promocional: str | None = None
    custo: str | None = None
    estoque: int | None = None
    peso: str | None = None
    largura: str | None = None
    altura: str | None = None
    profundidade: str | None = None
    codigo_barras: str = ""
    # Ex.: {"Tamanho": "M", "Cor": "Preto"}
    atributos: dict[str, str] = field(default_factory=dict)
    linha: int = 0


@dataclass
class Produto:
    grupo: str
    nome: str
    descricao: str = ""
    marca: str = ""
    handle: str = ""
    seo_titulo: str = ""
    seo_descricao: str = ""
    video: str = ""
    frete_gratis: bool = False
    categorias: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    imagens: list[str] = field(default_factory=list)
    variantes: list[Variante] = field(default_factory=list)
    linha: int = 0

    @property
    def nomes_atributos(self) -> list[str]:
        """Ordem dos atributos do produto, na ordem em que apareceram."""
        ordem: list[str] = []
        for variante in self.variantes:
            for nome in variante.atributos:
                if nome not in ordem:
                    ordem.append(nome)
        return ordem


def _extrair_atributos(bruto: dict[str, Any]) -> dict[str, str]:
    atributos: dict[str, str] = {}

    for campo, rotulo in (("tamanho", "Tamanho"), ("cor", "Cor")):
        valor = str(bruto.get(campo) or "").strip()
        if valor:
            atributos[rotulo] = valor

    for chave, valor in bruto.items():
        for prefixo in PREFIXOS_ATRIBUTO:
            if chave.startswith(prefixo) and str(valor or "").strip():
                rotulo = chave[len(prefixo):].replace("_", " ").strip().title()
                if rotulo:
                    atributos[rotulo] = str(valor).strip()
                break
    return atributos


def _linha_para_bruto(linha: dict[str, Any]) -> dict[str, Any]:
    """Renomeia as colunas da planilha para os campos internos."""
    bruto: dict[str, Any] = {}
    for coluna, valor in linha.items():
        if coluna is None:
            continue
        chave = normalizar_chave(str(coluna))
        if not chave:
            continue
        destino = MAPA_APELIDOS.get(chave, chave)
        # Primeira coluna vence: evita que "imagem" sobrescreva "imagens".
        if destino not in bruto or not str(bruto.get(destino) or "").strip():
            bruto[destino] = valor
    return bruto


def _ler_csv(caminho: Path) -> list[dict[str, Any]]:
    texto = caminho.read_text(encoding="utf-8-sig")
    if not texto.strip():
        return []
    try:
        dialeto = csv.Sniffer().sniff(texto[:4096], delimiters=",;\t")
        delimitador = dialeto.delimiter
    except csv.Error:
        delimitador = ";" if texto.count(";") > texto.count(",") else ","
    leitor = csv.DictReader(texto.splitlines(), delimiter=delimitador)
    return [dict(linha) for linha in leitor]


def _ler_json(caminho: Path) -> list[dict[str, Any]]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if isinstance(dados, dict):
        dados = dados.get("produtos") or dados.get("products") or []
    if not isinstance(dados, list):
        raise ErroCatalogo(f"{caminho}: esperava uma lista de produtos.")
    return dados


def carregar(caminho: Path | str) -> list[Produto]:
    """Le o arquivo e devolve os produtos agrupados por variante."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroCatalogo(f"Catalogo nao encontrado: {caminho}")

    if caminho.suffix.lower() == ".json":
        linhas = _ler_json(caminho)
    elif caminho.suffix.lower() in {".csv", ".tsv", ".txt"}:
        linhas = _ler_csv(caminho)
    else:
        raise ErroCatalogo(
            f"Formato nao suportado: {caminho.suffix}. Use .csv ou .json."
        )

    if not linhas:
        raise ErroCatalogo(f"{caminho} nao tem nenhuma linha de produto.")

    return agrupar(linhas)


def agrupar(linhas: Iterable[dict[str, Any]]) -> list[Produto]:
    """Converte linhas cruas em produtos com variantes."""
    produtos: dict[str, Produto] = {}

    for indice, linha_bruta in enumerate(linhas, start=2):  # 1 = cabecalho
        # No JSON, um item pode ja trazer suas variantes aninhadas.
        if isinstance(linha_bruta.get("variantes"), list) or isinstance(
            linha_bruta.get("variants"), list
        ):
            produto = _produto_aninhado(linha_bruta, indice)
            produtos[produto.grupo] = produto
            continue

        bruto = _linha_para_bruto(linha_bruta)
        nome = str(bruto.get("nome") or "").strip()
        grupo = str(bruto.get("grupo") or "").strip() or nome
        if not grupo:
            # Linha em branco no fim da planilha: ignora em silencio.
            if not any(str(v or "").strip() for v in bruto.values()):
                continue
            grupo = f"(sem nome) linha {indice}"

        produto = produtos.get(grupo)
        if produto is None:
            produto = Produto(
                grupo=grupo,
                nome=nome,
                descricao=str(bruto.get("descricao") or "").strip(),
                marca=str(bruto.get("marca") or "").strip(),
                handle=str(bruto.get("handle") or "").strip(),
                seo_titulo=str(bruto.get("seo_titulo") or "").strip(),
                seo_descricao=str(bruto.get("seo_descricao") or "").strip(),
                video=str(bruto.get("video") or "").strip(),
                frete_gratis=parse_bool(bruto.get("frete_gratis")),
                categorias=parse_lista(bruto.get("categorias")),
                tags=parse_lista(bruto.get("tags")),
                imagens=parse_lista(bruto.get("imagens")),
                linha=indice,
            )
            produtos[grupo] = produto
        else:
            # Campos de produto podem estar so na primeira linha do grupo;
            # se vierem repetidos nas outras, completamos o que faltar.
            produto.descricao = produto.descricao or str(bruto.get("descricao") or "").strip()
            produto.marca = produto.marca or str(bruto.get("marca") or "").strip()
            produto.nome = produto.nome or nome
            for imagem in parse_lista(bruto.get("imagens")):
                if imagem not in produto.imagens:
                    produto.imagens.append(imagem)
            for tag in parse_lista(bruto.get("tags")):
                if tag not in produto.tags:
                    produto.tags.append(tag)
            for categoria in parse_lista(bruto.get("categorias")):
                if categoria not in produto.categorias:
                    produto.categorias.append(categoria)

        produto.variantes.append(
            Variante(
                sku=str(bruto.get("sku") or "").strip(),
                preco=parse_decimal(bruto.get("preco")),
                preco_promocional=parse_decimal(bruto.get("preco_promocional")),
                custo=parse_decimal(bruto.get("custo")),
                estoque=parse_inteiro(bruto.get("estoque")),
                peso=parse_decimal(bruto.get("peso")),
                largura=parse_decimal(bruto.get("largura")),
                altura=parse_decimal(bruto.get("altura")),
                profundidade=parse_decimal(bruto.get("profundidade")),
                codigo_barras=str(bruto.get("codigo_barras") or "").strip(),
                atributos=_extrair_atributos(bruto),
                linha=indice,
            )
        )

    return list(produtos.values())


def _produto_aninhado(item: dict[str, Any], indice: int) -> Produto:
    bruto = _linha_para_bruto({k: v for k, v in item.items() if k not in {"variantes", "variants"}})
    nome = str(bruto.get("nome") or "").strip()
    produto = Produto(
        grupo=str(bruto.get("grupo") or "").strip() or nome,
        nome=nome,
        descricao=str(bruto.get("descricao") or "").strip(),
        marca=str(bruto.get("marca") or "").strip(),
        handle=str(bruto.get("handle") or "").strip(),
        seo_titulo=str(bruto.get("seo_titulo") or "").strip(),
        seo_descricao=str(bruto.get("seo_descricao") or "").strip(),
        video=str(bruto.get("video") or "").strip(),
        frete_gratis=parse_bool(bruto.get("frete_gratis")),
        categorias=parse_lista(bruto.get("categorias")),
        tags=parse_lista(bruto.get("tags")),
        imagens=parse_lista(bruto.get("imagens")),
        linha=indice,
    )
    for variante_bruta in item.get("variantes") or item.get("variants") or []:
        vb = _linha_para_bruto(variante_bruta)
        produto.variantes.append(
            Variante(
                sku=str(vb.get("sku") or "").strip(),
                preco=parse_decimal(vb.get("preco")),
                preco_promocional=parse_decimal(vb.get("preco_promocional")),
                custo=parse_decimal(vb.get("custo")),
                estoque=parse_inteiro(vb.get("estoque")),
                peso=parse_decimal(vb.get("peso")),
                largura=parse_decimal(vb.get("largura")),
                altura=parse_decimal(vb.get("altura")),
                profundidade=parse_decimal(vb.get("profundidade")),
                codigo_barras=str(vb.get("codigo_barras") or "").strip(),
                atributos=_extrair_atributos(vb),
                linha=indice,
            )
        )
    return produto
