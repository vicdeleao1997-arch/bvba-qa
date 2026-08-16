"""Testes de ponta a ponta da CLI contra a loja falsa local.

Cobre o caminho de maior risco do drop: subir como rascunho e publicar no
horario. Sobe um HTTPServer de verdade em porta efemera, entao exercita o
cliente HTTP inteiro -- headers, JSON, status.
"""

import contextlib
import io
import threading
import unittest
from datetime import datetime, timedelta
from http.server import HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import ferramentas.loja_falsa as loja_falsa
from agente_drop.cli import main
from agente_drop.relogio import fuso

CATALOGO = "catalogo/exemplo-drop.csv"


class BaseCLI(unittest.TestCase):
    def setUp(self):
        loja_falsa.PRODUTOS.clear()
        loja_falsa.CONTADOR.update({"produto": 1000, "variante": 5000, "imagem": 9000})

        self.servidor = HTTPServer(("localhost", 0), loja_falsa.Handler)
        self.porta = self.servidor.server_address[1]
        self.thread = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.thread.start()

        self.pasta = TemporaryDirectory()
        self.estado = str(Path(self.pasta.name) / "estado.json")
        self.relatorios = str(Path(self.pasta.name) / "relatorios")

        self.ambiente = mock.patch.dict("os.environ", {
            "NUVEMSHOP_API_BASE": f"http://localhost:{self.porta}",
            "NUVEMSHOP_STORE_ID": "123456",
            "NUVEMSHOP_ACCESS_TOKEN": "ensaio",
            "NUVEMSHOP_USER_AGENT": "Teste (qa@bvba.com.br)",
        })
        self.ambiente.start()

    def tearDown(self):
        self.ambiente.stop()
        self.servidor.shutdown()
        self.servidor.server_close()
        self.pasta.cleanup()

    def rodar(self, *args):
        """Executa a CLI e devolve (codigo de saida, texto impresso)."""
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = main([*args, "--estado", self.estado, "--relatorios", self.relatorios])
        return codigo, saida.getvalue()

    def subir(self):
        return self.rodar("subir", "--catalogo", CATALOGO, "--aplicar")


class TestFluxoCompleto(BaseCLI):
    def test_conferir_conecta(self):
        codigo, texto = self.rodar("conferir")
        self.assertEqual(codigo, 0)
        self.assertIn("OK: conectado", texto)

    def test_subir_cria_tudo_como_rascunho(self):
        codigo, texto = self.subir()
        self.assertEqual(codigo, 0)
        self.assertIn("3 criado(s)", texto)
        self.assertEqual(len(loja_falsa.PRODUTOS), 3)
        for produto in loja_falsa.PRODUTOS.values():
            self.assertIs(produto["published"], False)

    def test_subir_sem_aplicar_nao_escreve_nada(self):
        codigo, texto = self.rodar("subir", "--catalogo", CATALOGO)
        self.assertEqual(codigo, 0)
        self.assertIn("simulacao", texto)
        self.assertEqual(loja_falsa.PRODUTOS, {})

    def test_relatorio_e_gravado(self):
        self.subir()
        arquivos = sorted(p.name for p in Path(self.relatorios).iterdir())
        self.assertEqual(len(arquivos), 2)  # .md e .json
        conteudo = (Path(self.relatorios) / arquivos[1]).read_text(encoding="utf-8")
        self.assertIn("Relatorio do drop BVBA", conteudo)

    def test_publicar_agora_poe_no_ar(self):
        self.subir()
        codigo, texto = self.rodar("publicar", "--agora")
        self.assertEqual(codigo, 0)
        self.assertIn("Drop no ar", texto)
        self.assertTrue(all(p["published"] for p in loja_falsa.PRODUTOS.values()))

    def test_despublicar_exige_confirmacao(self):
        self.subir()
        self.rodar("publicar", "--agora")
        codigo, texto = self.rodar("despublicar")
        self.assertEqual(codigo, 1)
        self.assertIn("Confirme com", texto)
        self.assertTrue(all(p["published"] for p in loja_falsa.PRODUTOS.values()))

    def test_despublicar_com_sim_reverte(self):
        self.subir()
        self.rodar("publicar", "--agora")
        codigo, _ = self.rodar("despublicar", "--sim")
        self.assertEqual(codigo, 0)
        self.assertTrue(all(not p["published"] for p in loja_falsa.PRODUTOS.values()))

    def test_status_mostra_rascunho(self):
        self.subir()
        _, texto = self.rodar("status")
        self.assertIn("rascunho: 3", texto)
        self.assertIn("publicado: 0", texto)


class TestAgendamento(BaseCLI):
    """O comportamento que decide se o drop sai no horario certo."""

    def _horario(self, deslocamento_segundos):
        alvo = datetime.now(fuso()) + timedelta(seconds=deslocamento_segundos)
        return alvo.strftime("%Y-%m-%d %H:%M:%S")

    def test_espera_ate_o_horario_e_publica(self):
        self.subir()
        codigo, texto = self.rodar("publicar", "--as", self._horario(2))
        self.assertEqual(codigo, 0)
        self.assertIn("agendada", texto)
        self.assertTrue(all(p["published"] for p in loja_falsa.PRODUTOS.values()))

    def test_runner_atrasado_dentro_da_tolerancia_publica(self):
        """Cron de CI atrasa: perder o minuto exato nao pode cancelar o drop."""
        self.subir()
        codigo, texto = self.rodar(
            "publicar", "--as", self._horario(-600), "--tolerancia", "60"
        )
        self.assertEqual(codigo, 0)
        self.assertIn("dentro da tolerancia", texto)
        self.assertTrue(all(p["published"] for p in loja_falsa.PRODUTOS.values()))

    def test_atraso_absurdo_nao_publica(self):
        """Se o job so acordou 6 horas depois, publicar sozinho seria pior."""
        self.subir()
        codigo, texto = self.rodar(
            "publicar", "--as", self._horario(-6 * 3600), "--tolerancia", "120"
        )
        self.assertEqual(codigo, 1)
        self.assertIn("acima da tolerancia", texto)
        self.assertTrue(all(not p["published"] for p in loja_falsa.PRODUTOS.values()))

    def test_horario_sem_data_nunca_cai_no_passado(self):
        """'20:00' as 21h significa amanha, e nao 'publica agora'."""
        self.subir()
        agora = datetime.now(fuso())
        passado = (agora - timedelta(hours=1)).strftime("%H:%M")
        with mock.patch("agente_drop.cli.esperar_ate") as espera:
            codigo, texto = self.rodar("publicar", "--as", passado)
        self.assertEqual(codigo, 0)
        espera.assert_called_once()
        alvo = espera.call_args[0][0]
        self.assertGreater(alvo, agora)

    def test_publicar_sem_horario_nem_agora_recusa(self):
        self.subir()
        codigo, texto = self.rodar("publicar")
        self.assertEqual(codigo, 2)
        self.assertIn("--as", texto)
        self.assertTrue(all(not p["published"] for p in loja_falsa.PRODUTOS.values()))

    def test_publicar_sem_estado_nao_faz_nada(self):
        codigo, texto = self.rodar("publicar", "--agora")
        self.assertEqual(codigo, 1)
        self.assertIn("estado do drop esta vazio", texto)


class TestIdempotencia(BaseCLI):
    def test_rodar_duas_vezes_nao_duplica(self):
        self.subir()
        codigo, texto = self.subir()
        self.assertEqual(codigo, 0)
        self.assertIn("3 sem mudanca", texto)
        self.assertEqual(len(loja_falsa.PRODUTOS), 3)

    def test_subir_depois_de_publicar_nao_despublica(self):
        """Recorrigir uma descricao as 20h05 nao pode tirar a loja do ar."""
        self.subir()
        self.rodar("publicar", "--agora")
        self.rodar("subir", "--catalogo", CATALOGO, "--aplicar", "--forcar")
        self.assertTrue(all(p["published"] for p in loja_falsa.PRODUTOS.values()))


if __name__ == "__main__":
    unittest.main()
