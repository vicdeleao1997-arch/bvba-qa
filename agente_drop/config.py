"""Configuracao do agente: variaveis de ambiente e arquivo .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Fuso do lancamento. O Brasil nao tem horario de verao desde 2019, entao o
# offset fixo -03:00 e um fallback seguro caso o sistema nao tenha tzdata.
FUSO_PADRAO = "America/Sao_Paulo"

# A API v1 da Nuvemshop responde tanto em api.nuvemshop.com.br quanto em
# api.tiendanube.com. Lojas brasileiras usam a primeira.
BASE_PADRAO = "https://api.nuvemshop.com.br"
VERSAO_PADRAO = "v1"

# Idioma dos campos i18n da loja (name, description, handle...). Loja BR = "pt".
IDIOMA_PADRAO = "pt"


class ErroConfig(Exception):
    """Configuracao ausente ou invalida."""


@dataclass(frozen=True)
class Config:
    store_id: str
    access_token: str
    user_agent: str
    base: str = BASE_PADRAO
    versao: str = VERSAO_PADRAO
    idioma: str = IDIOMA_PADRAO
    fuso: str = FUSO_PADRAO
    # Endereco do painel, so para deixar os produtos clicaveis no relatorio.
    # Nao da para deduzir do store_id: o subdominio da loja e outro.
    admin_url: str = ""

    @property
    def url_base(self) -> str:
        return f"{self.base.rstrip('/')}/{self.versao}/{self.store_id}"

    def url(self, caminho: str) -> str:
        return f"{self.url_base}/{caminho.lstrip('/')}"

    def resumo(self) -> str:
        """Descricao segura para log: nunca inclui o token."""
        return f"loja={self.store_id} api={self.base}/{self.versao} idioma={self.idioma}"


def carregar_dotenv(caminho: Path | str = ".env") -> dict[str, str]:
    """Le um .env simples (CHAVE=valor por linha). Nao sobrescreve o ambiente."""
    caminho = Path(caminho)
    if not caminho.exists():
        return {}

    valores: dict[str, str] = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        valor = valor.strip()
        # Aceita aspas em volta do valor, como todo .env costuma permitir.
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        valores[chave.strip()] = valor
    return valores


def carregar_config(dotenv: Path | str = ".env") -> Config:
    """Monta a Config a partir do ambiente, com o .env como fallback."""
    do_arquivo = carregar_dotenv(dotenv)

    def ler(chave: str, padrao: str | None = None) -> str | None:
        return os.environ.get(chave) or do_arquivo.get(chave) or padrao

    store_id = ler("NUVEMSHOP_STORE_ID")
    token = ler("NUVEMSHOP_ACCESS_TOKEN")
    user_agent = ler("NUVEMSHOP_USER_AGENT")

    faltando = [
        nome
        for nome, valor in (
            ("NUVEMSHOP_STORE_ID", store_id),
            ("NUVEMSHOP_ACCESS_TOKEN", token),
        )
        if not valor
    ]
    if faltando:
        raise ErroConfig(
            "Faltam variaveis de ambiente: "
            + ", ".join(faltando)
            + ".\nCopie .env.exemplo para .env e preencha, ou exporte no shell."
        )

    if not user_agent:
        raise ErroConfig(
            "NUVEMSHOP_USER_AGENT e obrigatorio. A Nuvemshop responde 400 sem um "
            'User-Agent identificavel. Use o formato "BVBA Drop (email@dominio.com)".'
        )
    if "(" not in user_agent or "@" not in user_agent:
        raise ErroConfig(
            'NUVEMSHOP_USER_AGENT precisa conter um email de contato entre parenteses, '
            'ex.: "BVBA Drop (contato@bvba.com.br)".'
        )

    return Config(
        store_id=str(store_id),
        access_token=str(token),
        user_agent=user_agent,
        base=ler("NUVEMSHOP_API_BASE", BASE_PADRAO) or BASE_PADRAO,
        versao=ler("NUVEMSHOP_API_VERSION", VERSAO_PADRAO) or VERSAO_PADRAO,
        idioma=ler("NUVEMSHOP_IDIOMA", IDIOMA_PADRAO) or IDIOMA_PADRAO,
        fuso=ler("DROP_FUSO", FUSO_PADRAO) or FUSO_PADRAO,
        admin_url=(ler("NUVEMSHOP_ADMIN_URL", "") or "").rstrip("/"),
    )
