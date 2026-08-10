"""Cliente HTTP da API da Nuvemshop, so com a biblioteca padrao.

Detalhes da API que costumam derrubar integracao e estao tratados aqui:

* O header de autenticacao da v1 se chama ``Authentication`` (nao
  ``Authorization``). Mandar o nome errado devolve 401. As versoes datadas
  (ex.: ``2025-03``) usam ``Authorization``. Mandamos os dois -- o header extra
  e ignorado pela versao que nao o usa.
* ``User-Agent`` e obrigatorio e precisa identificar a aplicacao com um email.
  Sem ele a resposta e 400.
* O limite e um leaky bucket: balde de 40 requisicoes, vazando 2 por segundo.
  Estourar devolve 429 com ``X-Rate-Limit-Reset`` em milissegundos.
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Iterator

from .config import Config

TIMEOUT_PADRAO = 30.0
TENTATIVAS_PADRAO = 5

# Leaky bucket documentado pela Nuvemshop.
BALDE = 40
VAZAO_POR_SEGUNDO = 2.0

STATUS_RETENTAVEIS = frozenset({429, 500, 502, 503, 504})


class ErroNuvemshop(Exception):
    """Falha de chamada a API, com o corpo da resposta preservado."""

    def __init__(self, mensagem: str, status: int | None = None, corpo: Any = None):
        super().__init__(mensagem)
        self.status = status
        self.corpo = corpo

    def descricao(self) -> str:
        partes = [str(self)]
        if self.corpo:
            partes.append(f"resposta: {json.dumps(self.corpo, ensure_ascii=False)[:600]}")
        return " | ".join(partes)


class Limitador:
    """Token bucket espelhando o leaky bucket do servidor."""

    def __init__(
        self,
        capacidade: int = BALDE,
        vazao: float = VAZAO_POR_SEGUNDO,
        dormir: Callable[[float], None] = time.sleep,
        agora: Callable[[], float] = time.monotonic,
    ):
        self.capacidade = capacidade
        self.vazao = vazao
        self._dormir = dormir
        self._agora = agora
        # Comeca com o balde cheio, mas guardamos uma folga: se o processo
        # anterior gastou o balde, o 429 e tratado no cliente com backoff.
        self._tokens = float(capacidade)
        self._ultimo = agora()

    def aguardar(self) -> None:
        agora = self._agora()
        decorrido = agora - self._ultimo
        self._ultimo = agora
        self._tokens = min(self.capacidade, self._tokens + decorrido * self.vazao)

        if self._tokens < 1.0:
            espera = (1.0 - self._tokens) / self.vazao
            self._dormir(espera)
            self._ultimo = self._agora()
            self._tokens = 0.0
        else:
            self._tokens -= 1.0

    def penalizar(self) -> None:
        """Zera o balde local depois de um 429, para desacelerar de verdade."""
        self._tokens = 0.0
        self._ultimo = self._agora()


class ClienteNuvemshop:
    def __init__(
        self,
        config: Config,
        *,
        timeout: float = TIMEOUT_PADRAO,
        tentativas: int = TENTATIVAS_PADRAO,
        limitador: Limitador | None = None,
        dormir: Callable[[float], None] = time.sleep,
        abrir: Callable[..., Any] | None = None,
    ):
        self.config = config
        self.timeout = timeout
        self.tentativas = tentativas
        self.limitador = limitador if limitador is not None else Limitador(dormir=dormir)
        self._dormir = dormir
        self._abrir = abrir or urllib.request.urlopen
        self.chamadas = 0

    # ---------------------------------------------------------------- HTTP --

    def _headers(self) -> dict[str, str]:
        return {
            # v1 usa Authentication; versoes datadas usam Authorization.
            "Authentication": f"bearer {self.config.access_token}",
            "Authorization": f"bearer {self.config.access_token}",
            "User-Agent": self.config.user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def requisitar(
        self,
        metodo: str,
        caminho: str,
        *,
        corpo: Any = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[Any, dict[str, str]]:
        url = self.config.url(caminho)
        if params:
            limpos = {k: v for k, v in params.items() if v is not None}
            if limpos:
                url = f"{url}?{urllib.parse.urlencode(limpos)}"

        dados = None
        if corpo is not None:
            dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")

        ultimo_erro: Exception | None = None
        for tentativa in range(1, self.tentativas + 1):
            self.limitador.aguardar()
            requisicao = urllib.request.Request(
                url, data=dados, headers=self._headers(), method=metodo.upper()
            )
            try:
                self.chamadas += 1
                with self._abrir(requisicao, timeout=self.timeout) as resposta:
                    bruto = resposta.read().decode("utf-8") or "null"
                    headers = {k.lower(): v for k, v in dict(resposta.headers).items()}
                    return json.loads(bruto), headers

            except urllib.error.HTTPError as erro:
                bruto = erro.read().decode("utf-8", errors="replace")
                try:
                    payload = json.loads(bruto) if bruto else None
                except json.JSONDecodeError:
                    payload = bruto

                headers = {k.lower(): v for k, v in dict(erro.headers or {}).items()}

                if erro.code in STATUS_RETENTAVEIS and tentativa < self.tentativas:
                    if erro.code == 429:
                        self.limitador.penalizar()
                    self._dormir(self._espera(tentativa, erro.code, headers))
                    ultimo_erro = ErroNuvemshop(
                        f"{metodo} {caminho} -> HTTP {erro.code}", erro.code, payload
                    )
                    continue

                raise ErroNuvemshop(
                    f"{metodo} {caminho} -> HTTP {erro.code}", erro.code, payload
                ) from erro

            except (urllib.error.URLError, TimeoutError, OSError) as erro:
                if tentativa < self.tentativas:
                    self._dormir(self._espera(tentativa, None, {}))
                    ultimo_erro = ErroNuvemshop(f"{metodo} {caminho} -> rede: {erro}")
                    continue
                raise ErroNuvemshop(f"{metodo} {caminho} -> rede: {erro}") from erro

        raise ultimo_erro or ErroNuvemshop(f"{metodo} {caminho} falhou")

    def _espera(self, tentativa: int, status: int | None, headers: dict[str, str]) -> float:
        """Backoff exponencial com jitter, respeitando o que o servidor pedir."""
        if status == 429:
            reset = headers.get("x-rate-limit-reset")
            if reset:
                try:
                    # Vem em milissegundos.
                    return min(60.0, max(1.0, float(reset) / 1000.0))
                except ValueError:
                    pass
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                return min(60.0, max(1.0, float(retry_after)))
            except ValueError:
                pass
        return min(30.0, (2 ** (tentativa - 1))) + random.uniform(0, 0.5)

    # ------------------------------------------------------------- helpers --

    def get(self, caminho: str, **params: Any) -> Any:
        dados, _ = self.requisitar("GET", caminho, params=params)
        return dados

    def post(self, caminho: str, corpo: Any) -> Any:
        dados, _ = self.requisitar("POST", caminho, corpo=corpo)
        return dados

    def put(self, caminho: str, corpo: Any) -> Any:
        dados, _ = self.requisitar("PUT", caminho, corpo=corpo)
        return dados

    def delete(self, caminho: str) -> Any:
        dados, _ = self.requisitar("DELETE", caminho)
        return dados

    def paginar(self, caminho: str, **params: Any) -> Iterator[dict]:
        """Percorre todas as paginas de um recurso de listagem."""
        pagina = 1
        por_pagina = params.pop("per_page", 200)
        while True:
            dados, headers = self.requisitar(
                "GET", caminho, params={**params, "page": pagina, "per_page": por_pagina}
            )
            if not dados:
                return
            for item in dados:
                yield item
            # A API sinaliza continuidade pelo header Link rel="next"; o
            # tamanho da pagina e so o desempate se o header vier ausente.
            link = headers.get("link", "")
            if 'rel="next"' not in link and len(dados) < por_pagina:
                return
            pagina += 1

    # ------------------------------------------------------------ recursos --

    def loja(self) -> dict:
        return self.get("store")

    def listar_produtos(self, **params: Any) -> list[dict]:
        return list(self.paginar("products", **params))

    def buscar_produto(self, termo: str) -> list[dict]:
        """Busca por nome/SKU. A API faz match parcial, filtramos depois."""
        return self.get("products", q=termo, per_page=50) or []

    def obter_produto(self, produto_id: int) -> dict:
        return self.get(f"products/{produto_id}")

    def criar_produto(self, payload: dict) -> dict:
        return self.post("products", payload)

    def atualizar_produto(self, produto_id: int, payload: dict) -> dict:
        return self.put(f"products/{produto_id}", payload)

    def atualizar_variante(self, produto_id: int, variante_id: int, payload: dict) -> dict:
        return self.put(f"products/{produto_id}/variants/{variante_id}", payload)

    def criar_variante(self, produto_id: int, payload: dict) -> dict:
        return self.post(f"products/{produto_id}/variants", payload)

    def listar_imagens(self, produto_id: int) -> list[dict]:
        return self.get(f"products/{produto_id}/images") or []

    def adicionar_imagem(self, produto_id: int, payload: dict) -> dict:
        return self.post(f"products/{produto_id}/images", payload)

    def listar_categorias(self) -> list[dict]:
        return list(self.paginar("categories"))

    def criar_categoria(self, payload: dict) -> dict:
        return self.post("categories", payload)

    def definir_publicacao(self, produto_id: int, publicado: bool) -> dict:
        return self.atualizar_produto(produto_id, {"published": publicado})
