"""Utilidades de teste: HTTP falso e catalogo de brinquedo."""

from __future__ import annotations

import io
import json
import urllib.error

from agente_drop.catalogo import Produto, Variante
from agente_drop.config import Config


def config_teste(**extras) -> Config:
    base = dict(
        store_id="123456",
        access_token="token-de-teste",
        user_agent="Teste (qa@bvba.com.br)",
    )
    base.update(extras)
    return Config(**base)


class RespostaFalsa(io.BytesIO):
    def __init__(self, corpo, headers: dict[str, str] | None = None):
        super().__init__(json.dumps(corpo).encode("utf-8"))
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
        return False


def erro_http(status: int, corpo=None, headers: dict[str, str] | None = None):
    return urllib.error.HTTPError(
        url="https://api.nuvemshop.com.br/v1/123456/products",
        code=status,
        msg="erro",
        hdrs=headers or {},
        fp=io.BytesIO(json.dumps(corpo or {"erro": "falhou"}).encode("utf-8")),
    )


class HttpFalso:
    """Substitui urlopen. Cada item da fila e uma resposta ou uma excecao."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.requisicoes = []

    def __call__(self, requisicao, timeout=None):
        self.requisicoes.append(requisicao)
        if not self.respostas:
            raise AssertionError("HttpFalso ficou sem respostas na fila")
        proxima = self.respostas.pop(0)
        if isinstance(proxima, Exception):
            raise proxima
        return proxima


class LojaFalsa:
    """Nuvemshop de mentira, em memoria, para testar o agente ponta a ponta."""

    def __init__(self):
        self.produtos: dict[int, dict] = {}
        self.proximo_id = 100
        self.proximo_variante_id = 900
        self.falhar_em: dict[str, Exception] = {}
        self.chamadas: list[tuple[str, str]] = []

    def _novo_id(self) -> int:
        self.proximo_id += 1
        return self.proximo_id

    def _nova_variante(self, corpo: dict) -> dict:
        self.proximo_variante_id += 1
        return {**corpo, "id": self.proximo_variante_id}

    def __call__(self, requisicao, timeout=None):
        metodo = requisicao.get_method()
        caminho = requisicao.full_url.split("/123456/", 1)[1].split("?")[0]
        self.chamadas.append((metodo, caminho))

        gatilho = f"{metodo} {caminho}"
        if gatilho in self.falhar_em:
            raise self.falhar_em[gatilho]

        corpo = json.loads(requisicao.data.decode("utf-8")) if requisicao.data else {}
        partes = caminho.split("/")

        if metodo == "POST" and caminho == "products":
            produto_id = self._novo_id()
            registro = {
                **corpo,
                "id": produto_id,
                "images": [],
                "variants": [self._nova_variante(v) for v in corpo.get("variants", [])],
            }
            self.produtos[produto_id] = registro
            return RespostaFalsa(registro)

        if metodo == "GET" and len(partes) == 2 and partes[0] == "products":
            return RespostaFalsa(self.produtos[int(partes[1])])

        if metodo == "PUT" and len(partes) == 2 and partes[0] == "products":
            registro = self.produtos[int(partes[1])]
            registro.update({k: v for k, v in corpo.items() if k != "variants"})
            return RespostaFalsa(registro)

        if metodo == "POST" and len(partes) == 3 and partes[2] == "images":
            registro = self.produtos[int(partes[1])]
            imagem = {**corpo, "id": len(registro["images"]) + 1}
            registro["images"].append(imagem)
            return RespostaFalsa(imagem)

        if metodo == "POST" and len(partes) == 3 and partes[2] == "variants":
            registro = self.produtos[int(partes[1])]
            variante = self._nova_variante(corpo)
            registro["variants"].append(variante)
            return RespostaFalsa(variante)

        if metodo == "PUT" and len(partes) == 4 and partes[2] == "variants":
            registro = self.produtos[int(partes[1])]
            for indice, variante in enumerate(registro["variants"]):
                if variante["id"] == int(partes[3]):
                    registro["variants"][indice] = {**variante, **corpo}
                    return RespostaFalsa(registro["variants"][indice])
            raise erro_http(404, {"erro": "variante nao encontrada"})

        if metodo == "GET" and caminho == "store":
            return RespostaFalsa({"id": 123456, "name": {"pt": "BVBA"}})

        raise erro_http(404, {"erro": f"rota nao mapeada: {gatilho}"})


def produto_teste(nome="Camiseta Signature", sku="BVBA-1", **extras) -> Produto:
    campos = dict(
        grupo=nome,
        nome=nome,
        descricao="Malha pesada 240g.",
        marca="BVBA",
        imagens=[],
        variantes=[
            Variante(sku=sku, preco="199.90", estoque=10, peso="0.35", atributos={"Tamanho": "M"})
        ],
    )
    campos.update(extras)
    return Produto(**campos)
