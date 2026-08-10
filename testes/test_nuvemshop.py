import unittest

from agente_drop.nuvemshop import ClienteNuvemshop, ErroNuvemshop, Limitador
from testes.apoio import HttpFalso, RespostaFalsa, config_teste, erro_http


class RelogioFalso:
    def __init__(self):
        self.t = 0.0
        self.dormidas = []

    def agora(self):
        return self.t

    def dormir(self, segundos):
        self.dormidas.append(segundos)
        self.t += segundos


def cliente_com(respostas, **extras):
    http = HttpFalso(respostas)
    relogio = RelogioFalso()
    cliente = ClienteNuvemshop(
        config_teste(),
        abrir=http,
        dormir=relogio.dormir,
        limitador=Limitador(dormir=relogio.dormir, agora=relogio.agora),
        **extras,
    )
    return cliente, http, relogio


class TestHeaders(unittest.TestCase):
    def test_manda_authentication_e_authorization(self):
        """A v1 exige 'Authentication'; versoes datadas usam 'Authorization'."""
        cliente, http, _ = cliente_com([RespostaFalsa({"id": 1})])
        cliente.loja()
        headers = http.requisicoes[0].headers
        self.assertEqual(headers["Authentication"], "bearer token-de-teste")
        self.assertEqual(headers["Authorization"], "bearer token-de-teste")

    def test_user_agent_vai_junto(self):
        cliente, http, _ = cliente_com([RespostaFalsa({"id": 1})])
        cliente.loja()
        self.assertEqual(http.requisicoes[0].headers["User-agent"], "Teste (qa@bvba.com.br)")

    def test_url_montada_com_versao_e_loja(self):
        cliente, http, _ = cliente_com([RespostaFalsa({"id": 1})])
        cliente.loja()
        self.assertEqual(
            http.requisicoes[0].full_url, "https://api.nuvemshop.com.br/v1/123456/store"
        )


class TestRetentativas(unittest.TestCase):
    def test_429_espera_o_reset_do_servidor(self):
        cliente, _, relogio = cliente_com([
            erro_http(429, headers={"X-Rate-Limit-Reset": "4000"}),
            RespostaFalsa([{"id": 1}]),
        ])
        cliente.get("products")
        # 4000 ms -> 4 s.
        self.assertIn(4.0, relogio.dormidas)

    def test_500_e_retentado(self):
        cliente, http, _ = cliente_com([erro_http(500), RespostaFalsa({"id": 7})])
        self.assertEqual(cliente.loja(), {"id": 7})
        self.assertEqual(len(http.requisicoes), 2)

    def test_401_falha_na_hora_sem_retentar(self):
        cliente, http, _ = cliente_com([erro_http(401, {"code": 401})])
        with self.assertRaises(ErroNuvemshop) as ctx:
            cliente.loja()
        self.assertEqual(ctx.exception.status, 401)
        self.assertEqual(len(http.requisicoes), 1)

    def test_desiste_depois_do_limite_de_tentativas(self):
        cliente, http, _ = cliente_com([erro_http(500)] * 5, tentativas=3)
        with self.assertRaises(ErroNuvemshop):
            cliente.loja()
        self.assertEqual(len(http.requisicoes), 3)

    def test_erro_preserva_o_corpo_da_resposta(self):
        cliente, _, _ = cliente_com([erro_http(422, {"name": "ja existe"})])
        with self.assertRaises(ErroNuvemshop) as ctx:
            cliente.criar_produto({})
        self.assertEqual(ctx.exception.corpo, {"name": "ja existe"})
        self.assertIn("ja existe", ctx.exception.descricao())


class TestLimitador(unittest.TestCase):
    def test_balde_cheio_nao_espera(self):
        relogio = RelogioFalso()
        limitador = Limitador(capacidade=40, vazao=2.0, dormir=relogio.dormir, agora=relogio.agora)
        for _ in range(40):
            limitador.aguardar()
        self.assertEqual(relogio.dormidas, [])

    def test_balde_vazio_espera_a_vazao(self):
        relogio = RelogioFalso()
        limitador = Limitador(capacidade=2, vazao=2.0, dormir=relogio.dormir, agora=relogio.agora)
        limitador.aguardar()
        limitador.aguardar()
        limitador.aguardar()  # balde vazio: precisa esperar 1/2 s
        self.assertEqual(len(relogio.dormidas), 1)
        self.assertAlmostEqual(relogio.dormidas[0], 0.5, places=3)

    def test_balde_recarrega_com_o_tempo(self):
        relogio = RelogioFalso()
        limitador = Limitador(capacidade=2, vazao=2.0, dormir=relogio.dormir, agora=relogio.agora)
        limitador.aguardar()
        limitador.aguardar()
        relogio.t += 10  # tempo suficiente para reencher
        limitador.aguardar()
        self.assertEqual(relogio.dormidas, [])


class TestPaginacao(unittest.TestCase):
    def test_para_quando_a_pagina_vem_incompleta(self):
        cliente, http, _ = cliente_com([RespostaFalsa([{"id": 1}, {"id": 2}])])
        itens = list(cliente.paginar("products", per_page=200))
        self.assertEqual(len(itens), 2)
        self.assertEqual(len(http.requisicoes), 1)

    def test_segue_o_header_link_mesmo_com_pagina_incompleta(self):
        cliente, http, _ = cliente_com([
            RespostaFalsa([{"id": 1}], {"Link": '<...page=2>; rel="next"'}),
            RespostaFalsa([{"id": 2}]),
        ])
        itens = list(cliente.paginar("products", per_page=2))
        self.assertEqual([i["id"] for i in itens], [1, 2])
        self.assertEqual(len(http.requisicoes), 2)

    def test_pagina_cheia_sem_link_continua_ate_esvaziar(self):
        """Se um proxy comer o header Link, e melhor pedir de novo do que
        truncar a lista em silencio."""
        cliente, http, _ = cliente_com([
            RespostaFalsa([{"id": 1}]),
            RespostaFalsa([]),
        ])
        itens = list(cliente.paginar("products", per_page=1))
        self.assertEqual([i["id"] for i in itens], [1])
        self.assertEqual(len(http.requisicoes), 2)

    def test_lista_vazia_encerra(self):
        cliente, _, _ = cliente_com([RespostaFalsa([])])
        self.assertEqual(list(cliente.paginar("products")), [])


if __name__ == "__main__":
    unittest.main()
