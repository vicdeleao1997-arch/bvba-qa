"""Estado do drop: liga cada produto do catalogo ao ID criado na Nuvemshop.

E isso que torna o agente idempotente. Rodar duas vezes nao duplica produto:
na segunda vez ele reconhece o que ja subiu, pula o que nao mudou e atualiza o
resto. Tambem e a lista que o comando ``publicar`` usa as 20h.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ARQUIVO_PADRAO = ".estado_drop.json"


def agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ItemEstado:
    chave: str
    produto_id: int
    nome: str = ""
    handle: str = ""
    hash: str = ""
    variantes: dict[str, int] = field(default_factory=dict)  # sku -> variant_id
    imagens: list[str] = field(default_factory=list)         # referencias ja enviadas
    publicado: bool = False
    criado_em: str = ""
    atualizado_em: str = ""


@dataclass
class Estado:
    loja: str = ""
    itens: dict[str, ItemEstado] = field(default_factory=dict)
    caminho: Path = field(default=Path(ARQUIVO_PADRAO), compare=False)

    # ------------------------------------------------------------- io --

    @classmethod
    def carregar(cls, caminho: Path | str = ARQUIVO_PADRAO) -> "Estado":
        caminho = Path(caminho)
        if not caminho.exists():
            return cls(caminho=caminho)

        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError as erro:
            raise ValueError(
                f"{caminho} esta corrompido ({erro}). Renomeie o arquivo para o "
                "agente comecar um estado novo -- mas confira antes o que ja subiu "
                "no painel, para nao duplicar produto."
            ) from erro

        itens = {
            chave: ItemEstado(**valor) for chave, valor in (dados.get("itens") or {}).items()
        }
        return cls(loja=str(dados.get("loja") or ""), itens=itens, caminho=caminho)

    def salvar(self) -> None:
        """Grava de forma atomica: um Ctrl+C no meio nao corrompe o arquivo."""
        corpo = {
            "loja": self.loja,
            "atualizado_em": agora_iso(),
            "itens": {chave: asdict(item) for chave, item in self.itens.items()},
        }
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(self.caminho.parent),
            prefix=".estado-",
            suffix=".tmp",
            delete=False,
        )
        try:
            with tmp:
                json.dump(corpo, tmp, ensure_ascii=False, indent=2)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp.name, self.caminho)
        except BaseException:
            Path(tmp.name).unlink(missing_ok=True)
            raise

    # --------------------------------------------------------- consulta --

    def obter(self, chave: str) -> ItemEstado | None:
        return self.itens.get(chave)

    def registrar(self, item: ItemEstado) -> None:
        existente = self.itens.get(item.chave)
        item.criado_em = existente.criado_em if existente else agora_iso()
        item.atualizado_em = agora_iso()
        self.itens[item.chave] = item

    def por_id(self, produto_id: int) -> ItemEstado | None:
        for item in self.itens.values():
            if item.produto_id == produto_id:
                return item
        return None

    @property
    def ids(self) -> list[int]:
        return [item.produto_id for item in self.itens.values()]

    def marcar_publicacao(self, produto_id: int, publicado: bool) -> None:
        item = self.por_id(produto_id)
        if item:
            item.publicado = publicado
            item.atualizado_em = agora_iso()
