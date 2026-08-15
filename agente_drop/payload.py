"""Traducao do catalogo interno para o corpo JSON da API da Nuvemshop.

Regra inegociavel do drop: ``montar_produto`` sempre devolve
``published: false``. A publicacao e um passo separado e explicito
(``agente_drop publicar``), nunca um efeito colateral do upload.
"""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
from pathlib import Path

from .catalogo import Produto, Variante, slugificar

LIMITE_SEO_TITULO = 70
LIMITE_SEO_DESCRICAO = 160


def i18n(valor: str, idioma: str) -> dict[str, str]:
    return {idioma: valor}


def _resumir_texto(texto: str, limite: int) -> str:
    texto = " ".join((texto or "").split())
    if len(texto) <= limite:
        return texto
    corte = texto[: limite - 1]
    # Corta na ultima palavra inteira para nao deixar termo picado.
    if " " in corte:
        corte = corte[: corte.rfind(" ")]
    return corte.rstrip(" ,.;:") + "…"


def montar_seo(produto: Produto) -> tuple[str, str]:
    titulo = produto.seo_titulo or produto.nome
    if produto.marca and produto.marca.lower() not in titulo.lower():
        candidato = f"{titulo} | {produto.marca}"
        if len(candidato) <= LIMITE_SEO_TITULO:
            titulo = candidato

    descricao = produto.seo_descricao or produto.descricao or produto.nome
    return _resumir_texto(titulo, LIMITE_SEO_TITULO), _resumir_texto(
        descricao, LIMITE_SEO_DESCRICAO
    )


def montar_variante(
    variante: Variante, nomes_atributos: list[str], idioma: str
) -> dict:
    corpo: dict = {
        "price": variante.preco,
        "sku": variante.sku or None,
        "barcode": variante.codigo_barras or None,
        "weight": variante.peso,
        "width": variante.largura,
        "height": variante.altura,
        "depth": variante.profundidade,
        "cost": variante.custo,
        "promotional_price": variante.preco_promocional,
    }

    if variante.estoque is None:
        # Sem numero de estoque = venda sem controle, e nao "esgotado".
        corpo["stock_management"] = False
    else:
        corpo["stock_management"] = True
        corpo["stock"] = variante.estoque

    if nomes_atributos:
        corpo["values"] = [
            i18n(variante.atributos.get(nome, ""), idioma) for nome in nomes_atributos
        ]

    return {k: v for k, v in corpo.items() if v is not None}


def montar_produto(produto: Produto, idioma: str = "pt") -> dict:
    """Corpo do POST /products. Sempre rascunho."""
    seo_titulo, seo_descricao = montar_seo(produto)
    nomes_atributos = produto.nomes_atributos
    handle = produto.handle or slugificar(produto.nome or produto.grupo)

    corpo: dict = {
        "name": i18n(produto.nome, idioma),
        "description": i18n(produto.descricao, idioma),
        "handle": i18n(handle, idioma),
        "seo_title": seo_titulo,
        "seo_description": seo_descricao,
        # Trava do drop: nunca sai daqui como publicado.
        "published": False,
        "free_shipping": produto.frete_gratis,
        "variants": [
            montar_variante(v, nomes_atributos, idioma) for v in produto.variantes
        ],
    }

    if nomes_atributos:
        corpo["attributes"] = [i18n(nome, idioma) for nome in nomes_atributos]
    if produto.marca:
        corpo["brand"] = produto.marca
    if produto.tags:
        corpo["tags"] = ", ".join(produto.tags)
    if produto.video:
        corpo["video_url"] = produto.video

    return corpo


def montar_imagem(referencia: str, posicao: int, raiz: Path | str = ".") -> dict:
    """URL vira ``src``; arquivo local vira ``attachment`` em base64."""
    if referencia.lower().startswith(("http://", "https://")):
        return {"src": referencia, "position": posicao}

    caminho = Path(raiz) / referencia
    dados = caminho.read_bytes()
    tipo, _ = mimetypes.guess_type(caminho.name)
    if tipo and not tipo.startswith("image/"):
        raise ValueError(f"{caminho} nao parece ser uma imagem ({tipo}).")
    return {
        "attachment": base64.b64encode(dados).decode("ascii"),
        "filename": caminho.name,
        "position": posicao,
    }


def impressao_digital(produto: Produto, idioma: str = "pt") -> str:
    """Hash do conteudo do produto, para pular o que nao mudou entre execucoes."""
    corpo = montar_produto(produto, idioma)
    corpo["_imagens"] = list(produto.imagens)
    corpo["_categorias"] = list(produto.categorias)
    bruto = json.dumps(corpo, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()[:16]
