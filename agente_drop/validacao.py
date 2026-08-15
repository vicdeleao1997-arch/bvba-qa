"""Validacao do catalogo antes de qualquer chamada a API.

A ideia e falhar barato: tudo que a Nuvemshop rejeitaria (ou que sairia torto
na vitrine) e apontado aqui, com a linha da planilha, antes de subir nada.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .catalogo import Produto

# A Nuvemshop aceita no maximo 3 opcoes de variante por produto.
MAX_ATRIBUTOS = 3
MAX_NOME = 255

ERRO = "erro"
AVISO = "aviso"


@dataclass(frozen=True)
class Problema:
    nivel: str
    produto: str
    campo: str
    mensagem: str
    linha: int = 0

    def __str__(self) -> str:
        onde = f"linha {self.linha}" if self.linha else "-"
        return f"[{self.nivel.upper()}] {self.produto} ({onde}) {self.campo}: {self.mensagem}"


def _imagem_local(referencia: str) -> bool:
    return not referencia.lower().startswith(("http://", "https://", "data:"))


def validar(produtos: Iterable[Produto], *, raiz_imagens: Path | str = ".") -> list[Problema]:
    problemas: list[Problema] = []
    raiz = Path(raiz_imagens)
    skus_vistos: dict[str, int] = {}
    handles_vistos: dict[str, str] = {}

    produtos = list(produtos)
    if not produtos:
        return [Problema(ERRO, "-", "catalogo", "Nenhum produto encontrado no arquivo.")]

    for produto in produtos:
        rotulo = produto.nome or produto.grupo

        if not produto.nome.strip():
            problemas.append(
                Problema(ERRO, rotulo, "nome", "Produto sem nome.", produto.linha)
            )
        elif len(produto.nome) > MAX_NOME:
            problemas.append(
                Problema(
                    ERRO, rotulo, "nome",
                    f"Nome com {len(produto.nome)} caracteres (maximo {MAX_NOME}).",
                    produto.linha,
                )
            )

        if produto.handle:
            anterior = handles_vistos.get(produto.handle)
            if produto.handle in handles_vistos and anterior != produto.grupo:
                problemas.append(
                    Problema(
                        ERRO, rotulo, "handle",
                        f'URL "{produto.handle}" repetida (ja usada por "{anterior}").',
                        produto.linha,
                    )
                )
            handles_vistos[produto.handle] = produto.grupo

        if not produto.descricao.strip():
            problemas.append(
                Problema(AVISO, rotulo, "descricao", "Sem descricao.", produto.linha)
            )

        if not produto.imagens:
            problemas.append(
                Problema(
                    AVISO, rotulo, "imagens",
                    "Produto sem foto: vai pro ar como placeholder cinza.",
                    produto.linha,
                )
            )

        for imagem in produto.imagens:
            if _imagem_local(imagem) and not (raiz / imagem).exists():
                problemas.append(
                    Problema(
                        ERRO, rotulo, "imagens",
                        f"Arquivo de imagem nao encontrado: {raiz / imagem}",
                        produto.linha,
                    )
                )

        if not produto.variantes:
            problemas.append(
                Problema(ERRO, rotulo, "variantes", "Produto sem nenhuma variante/linha.", produto.linha)
            )
            continue

        nomes_atributos = produto.nomes_atributos
        if len(nomes_atributos) > MAX_ATRIBUTOS:
            problemas.append(
                Problema(
                    ERRO, rotulo, "atributos",
                    f"{len(nomes_atributos)} atributos ({', '.join(nomes_atributos)}); "
                    f"a Nuvemshop aceita no maximo {MAX_ATRIBUTOS}.",
                    produto.linha,
                )
            )

        combinacoes: dict[tuple[str, ...], int] = {}

        for variante in produto.variantes:
            onde = variante.linha or produto.linha
            nome_var = f"{rotulo} [{variante.sku or 'sem SKU'}]"

            if variante.preco is None:
                problemas.append(
                    Problema(ERRO, nome_var, "preco", "Variante sem preco.", onde)
                )
            elif float(variante.preco) <= 0:
                problemas.append(
                    Problema(ERRO, nome_var, "preco", f"Preco invalido: {variante.preco}.", onde)
                )

            if variante.preco_promocional is not None and variante.preco is not None:
                if float(variante.preco_promocional) >= float(variante.preco):
                    problemas.append(
                        Problema(
                            ERRO, nome_var, "preco_promocional",
                            f"Promocional ({variante.preco_promocional}) precisa ser menor "
                            f"que o preco cheio ({variante.preco}).",
                            onde,
                        )
                    )
                elif float(variante.preco_promocional) <= 0:
                    problemas.append(
                        Problema(ERRO, nome_var, "preco_promocional", "Valor invalido.", onde)
                    )

            if variante.estoque is not None and variante.estoque < 0:
                problemas.append(
                    Problema(ERRO, nome_var, "estoque", f"Estoque negativo: {variante.estoque}.", onde)
                )
            elif variante.estoque == 0:
                problemas.append(
                    Problema(
                        AVISO, nome_var, "estoque",
                        "Estoque zero: entra no ar esgotada.", onde,
                    )
                )

            if not variante.sku:
                problemas.append(
                    Problema(
                        AVISO, nome_var, "sku",
                        "Sem SKU: o agente nao consegue reconhecer essa variante "
                        "numa segunda execucao (risco de duplicar).",
                        onde,
                    )
                )
            elif variante.sku in skus_vistos:
                # Testar com `in`, e nao pela verdade do valor: linha 0
                # (catalogo JSON, sem numero de linha) e um valor valido.
                anterior = skus_vistos[variante.sku]
                onde_anterior = f"linha {anterior}" if anterior else "outro produto"
                problemas.append(
                    Problema(
                        ERRO, nome_var, "sku",
                        f'SKU "{variante.sku}" repetido (ja usado em {onde_anterior}).',
                        onde,
                    )
                )
            else:
                skus_vistos[variante.sku] = onde

            if variante.peso is None:
                problemas.append(
                    Problema(
                        AVISO, nome_var, "peso",
                        "Sem peso: o calculo de frete pode falhar no checkout.", onde,
                    )
                )

            # Todas as variantes precisam responder aos mesmos atributos.
            faltando = [n for n in nomes_atributos if n not in variante.atributos]
            if faltando:
                problemas.append(
                    Problema(
                        ERRO, nome_var, "atributos",
                        f"Faltam valores para: {', '.join(faltando)}. "
                        "Todas as variantes do produto precisam preencher as mesmas colunas.",
                        onde,
                    )
                )

            chave = tuple(variante.atributos.get(n, "") for n in nomes_atributos)
            if len(produto.variantes) > 1:
                if chave in combinacoes:
                    problemas.append(
                        Problema(
                            ERRO, nome_var, "atributos",
                            f"Combinacao {chave or '(unica)'} repetida "
                            f"(ja aparece na linha {combinacoes[chave]}).",
                            onde,
                        )
                    )
                else:
                    combinacoes[chave] = onde

    return problemas


def tem_erro(problemas: Iterable[Problema]) -> bool:
    return any(p.nivel == ERRO for p in problemas)


def resumir(problemas: Iterable[Problema]) -> tuple[int, int]:
    problemas = list(problemas)
    erros = sum(1 for p in problemas if p.nivel == ERRO)
    return erros, len(problemas) - erros
