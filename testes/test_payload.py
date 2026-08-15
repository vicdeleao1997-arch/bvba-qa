import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agente_drop.catalogo import Produto, Variante
from agente_drop.payload import (
    impressao_digital,
    montar_imagem,
    montar_produto,
    montar_seo,
    montar_variante,
)
from testes.apoio import produto_teste


class TestTravaDePublicacao(unittest.TestCase):
    """A regra que sustenta o drop inteiro: upload nunca publica."""

    def test_payload_sempre_sai_como_rascunho(self):
        corpo = montar_produto(produto_teste())
        self.assertIs(corpo["published"], False)

    def test_nem_mesmo_com_coluna_publicado_no_catalogo(self):
        produto = produto_teste()
        # Mesmo que alguem invente uma coluna "publicado" na planilha, ela
        # nao tem caminho ate o payload.
        produto.tags = ["publicado"]
        corpo = montar_produto(produto)
        self.assertIs(corpo["published"], False)


class TestProduto(unittest.TestCase):
    def test_campos_i18n(self):
        corpo = montar_produto(produto_teste(), idioma="pt")
        self.assertEqual(corpo["name"], {"pt": "Camiseta Signature"})
        self.assertEqual(corpo["handle"], {"pt": "camiseta-signature"})

    def test_atributos_e_valores_batem_na_ordem(self):
        produto = Produto(
            grupo="g", nome="Camiseta",
            variantes=[
                Variante(sku="A", preco="10", atributos={"Tamanho": "P", "Cor": "Preto"}),
                Variante(sku="B", preco="10", atributos={"Tamanho": "M", "Cor": "Preto"}),
            ],
        )
        corpo = montar_produto(produto)
        self.assertEqual(corpo["attributes"], [{"pt": "Tamanho"}, {"pt": "Cor"}])
        self.assertEqual(corpo["variants"][0]["values"], [{"pt": "P"}, {"pt": "Preto"}])
        self.assertEqual(corpo["variants"][1]["values"], [{"pt": "M"}, {"pt": "Preto"}])

    def test_tags_viram_string(self):
        corpo = montar_produto(produto_teste(tags=["drop01", "oversized"]))
        self.assertEqual(corpo["tags"], "drop01, oversized")

    def test_produto_sem_atributo_nao_manda_values(self):
        produto = Produto(grupo="g", nome="Bone", variantes=[Variante(sku="A", preco="10")])
        corpo = montar_produto(produto)
        self.assertNotIn("attributes", corpo)
        self.assertNotIn("values", corpo["variants"][0])


class TestVariante(unittest.TestCase):
    def test_estoque_informado_liga_controle(self):
        corpo = montar_variante(Variante(sku="A", preco="10", estoque=5), [], "pt")
        self.assertTrue(corpo["stock_management"])
        self.assertEqual(corpo["stock"], 5)

    def test_estoque_ausente_desliga_controle(self):
        """Sem numero de estoque a peca vende livre, e nao aparece esgotada."""
        corpo = montar_variante(Variante(sku="A", preco="10", estoque=None), [], "pt")
        self.assertFalse(corpo["stock_management"])
        self.assertNotIn("stock", corpo)

    def test_estoque_zero_e_preservado(self):
        corpo = montar_variante(Variante(sku="A", preco="10", estoque=0), [], "pt")
        self.assertTrue(corpo["stock_management"])
        self.assertEqual(corpo["stock"], 0)

    def test_campos_vazios_sao_omitidos(self):
        corpo = montar_variante(Variante(sku="", preco="10"), [], "pt")
        self.assertNotIn("sku", corpo)
        self.assertNotIn("barcode", corpo)


class TestSeo(unittest.TestCase):
    def test_marca_entra_no_titulo(self):
        titulo, _ = montar_seo(produto_teste())
        self.assertEqual(titulo, "Camiseta Signature | BVBA")

    def test_titulo_longo_e_cortado_em_palavra_inteira(self):
        produto = produto_teste(nome="Camiseta " + "muito " * 30 + "longa")
        titulo, _ = montar_seo(produto)
        self.assertLessEqual(len(titulo), 70)
        self.assertTrue(titulo.endswith("…"))

    def test_descricao_seo_vem_da_descricao(self):
        _, descricao = montar_seo(produto_teste())
        self.assertEqual(descricao, "Malha pesada 240g.")

    def test_seo_manual_tem_prioridade(self):
        produto = produto_teste(seo_titulo="Meu titulo", seo_descricao="Minha descricao")
        titulo, descricao = montar_seo(produto)
        self.assertEqual(titulo, "Meu titulo | BVBA")
        self.assertEqual(descricao, "Minha descricao")


class TestImagem(unittest.TestCase):
    def test_url_vira_src(self):
        corpo = montar_imagem("https://exemplo.com/a.jpg", 1)
        self.assertEqual(corpo, {"src": "https://exemplo.com/a.jpg", "position": 1})

    def test_arquivo_local_vira_base64(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "foto.jpg"
            arquivo.write_bytes(b"\xff\xd8\xff\xe0conteudo")
            corpo = montar_imagem("foto.jpg", 2, pasta)
        self.assertEqual(corpo["filename"], "foto.jpg")
        self.assertEqual(corpo["position"], 2)
        self.assertNotIn("src", corpo)

    def test_arquivo_inexistente_falha_alto(self):
        with self.assertRaises(OSError):
            montar_imagem("nao-existe.jpg", 1, "/tmp")

    def test_arquivo_que_nao_e_imagem_e_recusado(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "planilha.pdf"
            arquivo.write_bytes(b"%PDF-1.4")
            with self.assertRaises(ValueError):
                montar_imagem("planilha.pdf", 1, pasta)


class TestImpressaoDigital(unittest.TestCase):
    def test_mesmo_produto_mesmo_hash(self):
        self.assertEqual(impressao_digital(produto_teste()), impressao_digital(produto_teste()))

    def test_preco_diferente_muda_hash(self):
        outro = produto_teste()
        outro.variantes[0].preco = "249.90"
        self.assertNotEqual(impressao_digital(produto_teste()), impressao_digital(outro))

    def test_imagem_nova_muda_hash(self):
        outro = produto_teste(imagens=["https://exemplo.com/nova.jpg"])
        self.assertNotEqual(impressao_digital(produto_teste()), impressao_digital(outro))


if __name__ == "__main__":
    unittest.main()
