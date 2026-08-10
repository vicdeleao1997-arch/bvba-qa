import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agente_drop.estado import Estado, ItemEstado


class TestEstado(unittest.TestCase):
    def test_arquivo_inexistente_comeca_vazio(self):
        with TemporaryDirectory() as pasta:
            estado = Estado.carregar(Path(pasta) / "novo.json")
        self.assertEqual(estado.itens, {})

    def test_salva_e_recarrega(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "estado.json"
            estado = Estado.carregar(caminho)
            estado.loja = "123456"
            estado.registrar(ItemEstado(chave="sku:A", produto_id=10, nome="Camiseta"))
            estado.salvar()

            recarregado = Estado.carregar(caminho)

        self.assertEqual(recarregado.loja, "123456")
        self.assertEqual(recarregado.obter("sku:A").produto_id, 10)

    def test_registrar_preserva_a_data_de_criacao(self):
        with TemporaryDirectory() as pasta:
            estado = Estado.carregar(Path(pasta) / "e.json")
            estado.registrar(ItemEstado(chave="sku:A", produto_id=10))
            criado_em = estado.obter("sku:A").criado_em
            estado.registrar(ItemEstado(chave="sku:A", produto_id=10, nome="mudou"))

        self.assertEqual(estado.obter("sku:A").criado_em, criado_em)
        self.assertEqual(estado.obter("sku:A").nome, "mudou")

    def test_busca_por_id(self):
        with TemporaryDirectory() as pasta:
            estado = Estado.carregar(Path(pasta) / "e.json")
            estado.registrar(ItemEstado(chave="sku:A", produto_id=77, nome="X"))
        self.assertEqual(estado.por_id(77).nome, "X")
        self.assertIsNone(estado.por_id(1))

    def test_marcar_publicacao(self):
        with TemporaryDirectory() as pasta:
            estado = Estado.carregar(Path(pasta) / "e.json")
            estado.registrar(ItemEstado(chave="sku:A", produto_id=77))
            estado.marcar_publicacao(77, True)
        self.assertTrue(estado.obter("sku:A").publicado)

    def test_arquivo_corrompido_avisa_em_vez_de_apagar(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "e.json"
            caminho.write_text("{isso nao e json", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                Estado.carregar(caminho)
        self.assertIn("corrompido", str(ctx.exception))

    def test_gravacao_nao_deixa_arquivo_temporario_para_tras(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "e.json"
            estado = Estado.carregar(caminho)
            estado.registrar(ItemEstado(chave="sku:A", produto_id=1))
            estado.salvar()
            restantes = [p.name for p in Path(pasta).iterdir()]

        self.assertEqual(restantes, ["e.json"])

    def test_json_gravado_e_legivel_por_humano(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "e.json"
            estado = Estado.carregar(caminho)
            estado.registrar(ItemEstado(chave="sku:A", produto_id=1, nome="Camiseta"))
            estado.salvar()
            corpo = json.loads(caminho.read_text(encoding="utf-8"))

        self.assertIn("itens", corpo)
        self.assertIn("atualizado_em", corpo)


if __name__ == "__main__":
    unittest.main()
