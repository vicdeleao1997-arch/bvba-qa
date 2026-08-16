"""Orquestracao do drop: planejar, subir como rascunho, publicar, reverter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from .catalogo import Produto, slugificar
from .config import Config
from .estado import Estado, ItemEstado
from .nuvemshop import ClienteNuvemshop, ErroNuvemshop
from .payload import impressao_digital, montar_imagem, montar_produto, montar_variante

CRIAR = "criar"
ATUALIZAR = "atualizar"
PULAR = "pular"

Log = Callable[[str], None]


def _silencio(_: str) -> None:
    pass


@dataclass
class Acao:
    tipo: str
    produto: Produto
    chave: str
    produto_id: int | None = None
    motivo: str = ""

    @property
    def rotulo(self) -> str:
        return self.produto.nome or self.produto.grupo


@dataclass
class Resultado:
    acao: Acao
    ok: bool
    produto_id: int | None = None
    imagens_enviadas: int = 0
    imagens_falhas: list[str] = field(default_factory=list)
    erro: str = ""


@dataclass
class Relatorio:
    resultados: list[Resultado] = field(default_factory=list)
    chamadas_api: int = 0

    @property
    def criados(self) -> list[Resultado]:
        return [r for r in self.resultados if r.ok and r.acao.tipo == CRIAR]

    @property
    def atualizados(self) -> list[Resultado]:
        return [r for r in self.resultados if r.ok and r.acao.tipo == ATUALIZAR]

    @property
    def pulados(self) -> list[Resultado]:
        return [r for r in self.resultados if r.ok and r.acao.tipo == PULAR]

    @property
    def falhas(self) -> list[Resultado]:
        return [r for r in self.resultados if not r.ok]


def chave_do_produto(produto: Produto) -> str:
    """Identidade estavel do produto entre execucoes.

    Preferimos o SKU da primeira variante, que e o que o lojista controla; se
    nao houver SKU, usamos o handle/slug do nome.
    """
    for variante in produto.variantes:
        if variante.sku:
            return f"sku:{variante.sku}"
    return f"handle:{produto.handle or slugificar(produto.nome or produto.grupo)}"


class AgenteDrop:
    def __init__(
        self,
        cliente: ClienteNuvemshop,
        config: Config,
        estado: Estado,
        *,
        raiz_imagens: Path | str = ".",
        log: Log = _silencio,
    ):
        self.cliente = cliente
        self.config = config
        self.estado = estado
        self.raiz_imagens = Path(raiz_imagens)
        self.log = log

    # ------------------------------------------------------------ plano --

    def planejar(self, produtos: Iterable[Produto], *, forcar: bool = False) -> list[Acao]:
        acoes: list[Acao] = []
        for produto in produtos:
            chave = chave_do_produto(produto)
            item = self.estado.obter(chave)
            digital = impressao_digital(produto, self.config.idioma)

            if item is None:
                acoes.append(Acao(CRIAR, produto, chave, motivo="produto novo"))
            elif forcar:
                acoes.append(
                    Acao(ATUALIZAR, produto, chave, item.produto_id, "reenvio forcado")
                )
            elif item.hash != digital:
                acoes.append(
                    Acao(ATUALIZAR, produto, chave, item.produto_id, "conteudo mudou")
                )
            else:
                acoes.append(
                    Acao(PULAR, produto, chave, item.produto_id, "sem alteracao")
                )
        return acoes

    # ---------------------------------------------------------- execucao --

    def executar(self, acoes: Iterable[Acao]) -> Relatorio:
        relatorio = Relatorio()
        for acao in acoes:
            if acao.tipo == PULAR:
                relatorio.resultados.append(
                    Resultado(acao, ok=True, produto_id=acao.produto_id)
                )
                continue
            try:
                relatorio.resultados.append(self._aplicar(acao))
            except ErroNuvemshop as erro:
                self.log(f"  x {acao.rotulo}: {erro.descricao()}")
                relatorio.resultados.append(Resultado(acao, ok=False, erro=erro.descricao()))
            except Exception as erro:  # noqa: BLE001 - um produto ruim nao derruba o drop
                self.log(f"  x {acao.rotulo}: {erro}")
                relatorio.resultados.append(Resultado(acao, ok=False, erro=str(erro)))
            finally:
                # Salva a cada produto: queda no meio nao perde o que ja subiu.
                self.estado.salvar()

        relatorio.chamadas_api = self.cliente.chamadas
        return relatorio

    def _aplicar(self, acao: Acao) -> Resultado:
        produto = acao.produto
        corpo = montar_produto(produto, self.config.idioma)
        assert corpo["published"] is False, "payload de upload nunca pode ir publicado"

        if acao.tipo == CRIAR:
            self.log(f"  + criando {acao.rotulo} ({len(produto.variantes)} variante(s))")
            criado = self.cliente.criar_produto(corpo)
            produto_id = int(criado["id"])
        else:
            produto_id = int(acao.produto_id or 0)
            self.log(f"  ~ atualizando {acao.rotulo} (#{produto_id})")
            # Duas exclusoes deliberadas:
            #  - "variants": tem endpoint proprio; mandar aqui recriaria tudo.
            #  - "published": o update nao opina sobre visibilidade. Corrigir
            #    uma descricao as 20h05, com a loja no ar, nao pode derrubar o
            #    produto de volta para rascunho.
            corpo_update = {
                k: v for k, v in corpo.items() if k not in {"variants", "published"}
            }
            criado = self.cliente.atualizar_produto(produto_id, corpo_update)
            self._sincronizar_variantes(produto_id, produto, criado)
            criado = self.cliente.obter_produto(produto_id)

        item = self.estado.obter(acao.chave) or ItemEstado(chave=acao.chave, produto_id=produto_id)
        item.produto_id = produto_id
        item.nome = produto.nome
        item.handle = _texto_i18n(criado.get("handle"), self.config.idioma)
        item.hash = impressao_digital(produto, self.config.idioma)
        item.publicado = bool(criado.get("published", False))
        item.variantes = {
            str(v.get("sku") or ""): int(v["id"])
            for v in criado.get("variants", [])
            if v.get("sku")
        }

        enviadas, falhas = self._enviar_imagens(produto_id, produto, item)
        self.estado.registrar(item)

        return Resultado(
            acao,
            ok=not falhas,
            produto_id=produto_id,
            imagens_enviadas=enviadas,
            imagens_falhas=falhas,
            erro="" if not falhas else f"{len(falhas)} imagem(ns) falharam",
        )

    def _sincronizar_variantes(self, produto_id: int, produto: Produto, atual: dict) -> None:
        """Atualiza preco/estoque das variantes existentes e cria as novas."""
        nomes = produto.nomes_atributos
        por_sku = {
            str(v.get("sku") or ""): int(v["id"])
            for v in atual.get("variants", [])
            if v.get("sku")
        }
        for variante in produto.variantes:
            corpo = montar_variante(variante, nomes, self.config.idioma)
            existente = por_sku.get(variante.sku) if variante.sku else None
            if existente:
                self.cliente.atualizar_variante(produto_id, existente, corpo)
            else:
                self.cliente.criar_variante(produto_id, corpo)

    def _enviar_imagens(
        self, produto_id: int, produto: Produto, item: ItemEstado
    ) -> tuple[int, list[str]]:
        """Envia so o que ainda nao foi enviado, uma imagem por requisicao.

        Requisicao separada por imagem para que uma foto quebrada nao invalide
        o produto inteiro -- e para poder retomar de onde parou.
        """
        pendentes = [i for i in produto.imagens if i not in item.imagens]
        if not pendentes:
            return 0, []

        posicao_inicial = len(item.imagens) + 1
        enviadas = 0
        falhas: list[str] = []

        for deslocamento, referencia in enumerate(pendentes):
            try:
                corpo = montar_imagem(referencia, posicao_inicial + deslocamento, self.raiz_imagens)
                self.cliente.adicionar_imagem(produto_id, corpo)
                item.imagens.append(referencia)
                enviadas += 1
            except (ErroNuvemshop, OSError, ValueError) as erro:
                self.log(f"    ! imagem {referencia}: {erro}")
                falhas.append(f"{referencia}: {erro}")

        return enviadas, falhas

    # -------------------------------------------------------- publicacao --

    def publicar(self, *, publicado: bool = True, apenas: Iterable[int] | None = None) -> list[tuple[int, bool, str]]:
        """Liga (ou desliga) a vitrine dos produtos do drop.

        Devolve (produto_id, ok, mensagem) por produto.
        """
        alvos = list(apenas) if apenas is not None else self.estado.ids
        resultados: list[tuple[int, bool, str]] = []

        for produto_id in alvos:
            item = self.estado.por_id(produto_id)
            rotulo = item.nome if item else str(produto_id)
            try:
                self.cliente.definir_publicacao(produto_id, publicado)
                self.estado.marcar_publicacao(produto_id, publicado)
                resultados.append((produto_id, True, rotulo))
                self.log(f"  {'✔' if publicado else '⏸'} {rotulo} (#{produto_id})")
            except ErroNuvemshop as erro:
                resultados.append((produto_id, False, f"{rotulo}: {erro.descricao()}"))
                self.log(f"  x {rotulo} (#{produto_id}): {erro.descricao()}")

        self.estado.salvar()
        return resultados


def _texto_i18n(valor, idioma: str) -> str:
    if isinstance(valor, dict):
        return str(valor.get(idioma) or next(iter(valor.values()), "") or "")
    return str(valor or "")
