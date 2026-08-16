"""Nuvemshop de mentira, local, para ensaiar o drop sem tocar na loja real.

    # terminal 1
    python3 ferramentas/loja_falsa.py

    # terminal 2
    NUVEMSHOP_API_BASE=http://localhost:8799 \
    NUVEMSHOP_STORE_ID=123456 \
    NUVEMSHOP_ACCESS_TOKEN=ensaio \
    NUVEMSHOP_USER_AGENT="Ensaio (qa@bvba.com.br)" \
    python3 -m agente_drop subir --catalogo catalogo/exemplo-drop.csv \
        --estado /tmp/ensaio.json --aplicar

Implementa o suficiente da API para o agente rodar ponta a ponta: criar e
atualizar produto, variantes, imagens e o flag de publicacao. Guarda tudo em
memoria e imprime o que recebe.
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

PORTA = 8799

PRODUTOS: dict[int, dict] = {}
CONTADOR = {"produto": 1000, "variante": 5000, "imagem": 9000}


def _proximo(tipo: str) -> int:
    CONTADOR[tipo] += 1
    return CONTADOR[tipo]


def _rotulo(valor) -> str:
    if isinstance(valor, dict):
        return str(valor.get("pt") or next(iter(valor.values()), ""))
    return str(valor or "")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):  # silencia o log padrao, barulhento demais
        pass

    # ------------------------------------------------------------ apoio --

    def _corpo(self) -> dict:
        tamanho = int(self.headers.get("Content-Length") or 0)
        if not tamanho:
            return {}
        return json.loads(self.rfile.read(tamanho).decode("utf-8"))

    def _responder(self, status: int, corpo) -> None:
        bruto = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(bruto)))
        self.send_header("X-Rate-Limit-Limit", "40")
        self.end_headers()
        self.wfile.write(bruto)

    def _autorizado(self) -> bool:
        """Reproduz as duas recusas classicas da API real."""
        if not self.headers.get("Authentication") and not self.headers.get("Authorization"):
            self._responder(401, {"code": 401, "message": "sem header Authentication"})
            return False
        agente = self.headers.get("User-Agent") or ""
        if "@" not in agente:
            self._responder(400, {"code": 400, "message": "User-Agent sem email de contato"})
            return False
        return True

    def _rota(self) -> str:
        return re.sub(r"^/v1/\d+/", "", self.path.split("?")[0])

    # ---------------------------------------------------------- metodos --

    def do_GET(self):
        if not self._autorizado():
            return
        rota = self._rota()

        if rota == "store":
            return self._responder(200, {
                "id": 123456,
                "name": {"pt": "BVBA (ensaio local)"},
                "main_currency": "BRL",
                "main_language": "pt",
            })

        if rota == "products":
            return self._responder(200, list(PRODUTOS.values()))

        casado = re.fullmatch(r"products/(\d+)", rota)
        if casado:
            produto = PRODUTOS.get(int(casado.group(1)))
            if not produto:
                return self._responder(404, {"code": 404, "message": "nao encontrado"})
            return self._responder(200, produto)

        casado = re.fullmatch(r"products/(\d+)/images", rota)
        if casado:
            produto = PRODUTOS.get(int(casado.group(1)), {})
            return self._responder(200, produto.get("images", []))

        self._responder(404, {"code": 404, "message": f"rota nao mapeada: {rota}"})

    def do_POST(self):
        if not self._autorizado():
            return
        rota = self._rota()
        corpo = self._corpo()

        if rota == "products":
            produto_id = _proximo("produto")
            produto = {
                **corpo,
                "id": produto_id,
                "images": [],
                "variants": [
                    {**v, "id": _proximo("variante")} for v in corpo.get("variants", [])
                ],
            }
            PRODUTOS[produto_id] = produto
            estado = "PUBLICADO" if produto.get("published") else "rascunho"
            print(f"  + produto #{produto_id} [{estado}] {_rotulo(produto.get('name'))} "
                  f"({len(produto['variants'])} variante(s))")
            return self._responder(201, produto)

        casado = re.fullmatch(r"products/(\d+)/images", rota)
        if casado:
            produto = PRODUTOS[int(casado.group(1))]
            # O base64 do anexo poluiria o log; guardamos so o tamanho.
            anexo = corpo.pop("attachment", None)
            imagem = {**corpo, "id": _proximo("imagem")}
            if anexo:
                imagem["_bytes_recebidos"] = len(anexo)
            produto["images"].append(imagem)
            origem = imagem.get("src") or imagem.get("filename")
            print(f"    . imagem em #{produto['id']}: {origem}")
            return self._responder(201, imagem)

        casado = re.fullmatch(r"products/(\d+)/variants", rota)
        if casado:
            produto = PRODUTOS[int(casado.group(1))]
            variante = {**corpo, "id": _proximo("variante")}
            produto["variants"].append(variante)
            print(f"    . variante nova em #{produto['id']}: {variante.get('sku')}")
            return self._responder(201, variante)

        self._responder(404, {"code": 404, "message": f"rota nao mapeada: {rota}"})

    def do_PUT(self):
        if not self._autorizado():
            return
        rota = self._rota()
        corpo = self._corpo()

        casado = re.fullmatch(r"products/(\d+)", rota)
        if casado:
            produto = PRODUTOS.get(int(casado.group(1)))
            if not produto:
                return self._responder(404, {"code": 404, "message": "nao encontrado"})
            if "published" in corpo and len(corpo) == 1:
                estado = "PUBLICADO" if corpo["published"] else "despublicado"
                print(f"  * #{produto['id']} {_rotulo(produto.get('name'))} -> {estado}")
            produto.update({k: v for k, v in corpo.items() if k != "variants"})
            return self._responder(200, produto)

        casado = re.fullmatch(r"products/(\d+)/variants/(\d+)", rota)
        if casado:
            produto = PRODUTOS[int(casado.group(1))]
            alvo = int(casado.group(2))
            for indice, variante in enumerate(produto["variants"]):
                if variante["id"] == alvo:
                    produto["variants"][indice] = {**variante, **corpo}
                    print(f"    ~ variante #{alvo}: preco {corpo.get('price')}")
                    return self._responder(200, produto["variants"][indice])
            return self._responder(404, {"code": 404, "message": "variante nao encontrada"})

        self._responder(404, {"code": 404, "message": f"rota nao mapeada: {rota}"})


def main() -> None:
    servidor = HTTPServer(("localhost", PORTA), Handler)
    print(f"Loja falsa em http://localhost:{PORTA} (Ctrl+C para parar)")
    print("Use NUVEMSHOP_API_BASE=http://localhost:%d e store id 123456.\n" % PORTA)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado. Produtos criados no ensaio:", len(PRODUTOS))


if __name__ == "__main__":
    main()
