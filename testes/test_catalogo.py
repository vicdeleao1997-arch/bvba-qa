import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agente_drop.catalogo import (
    agrupar,
    carregar,
    parse_bool,
    parse_decimal,
    parse_inteiro,
    parse_lista,
    slugificar,
)


class TestParsers(unittest.TestCase):
    def test_preco_brasileiro_com_milhar(self):
        self.assertEqual(parse_decimal("R$ 1.299,90"), "1299.90")

    def test_preco_com_virgula_decimal(self):
        self.assertEqual(parse_decimal("199,9"), "199.90")

    def test_preco_com_ponto_decimal(self):
        self.assertEqual(parse_decimal("199.9"), "199.90")

    def test_preco_numerico(self):
        self.assertEqual(parse_decimal(199.9), "199.90")

    def test_preco_vazio_vira_none(self):
        self.assertIsNone(parse_decimal(""))
        self.assertIsNone(parse_decimal(None))
        self.assertIsNone(parse_decimal("grátis"))

    def test_inteiro_ignora_texto(self):
        self.assertEqual(parse_inteiro("12 un"), 12)
        self.assertEqual(parse_inteiro("-3"), -3)
        self.assertIsNone(parse_inteiro(""))

    def test_bool_aceita_sim(self):
        self.assertTrue(parse_bool("sim"))
        self.assertTrue(parse_bool("X"))
        self.assertFalse(parse_bool("nao"))
        self.assertFalse(parse_bool(""))

    def test_lista_separadores(self):
        self.assertEqual(parse_lista("a|b|c"), ["a", "b", "c"])
        self.assertEqual(parse_lista("a, b"), ["a", "b"])
        self.assertEqual(parse_lista(""), [])

    def test_slug_remove_acento(self):
        self.assertEqual(slugificar("Camiseta Oversized Signature"), "camiseta-oversized-signature")
        self.assertEqual(slugificar("Calça Cargo Tático"), "calca-cargo-tatico")


class TestAgrupamento(unittest.TestCase):
    def test_linhas_do_mesmo_nome_viram_variantes(self):
        produtos = agrupar([
            {"nome": "Camiseta", "sku": "C-P", "preco": "199,90", "tamanho": "P"},
            {"nome": "Camiseta", "sku": "C-M", "preco": "199,90", "tamanho": "M"},
            {"nome": "Bone", "sku": "B-U", "preco": "129,90", "tamanho": "Unico"},
        ])
        self.assertEqual(len(produtos), 2)
        self.assertEqual(len(produtos[0].variantes), 2)
        self.assertEqual(produtos[0].nomes_atributos, ["Tamanho"])

    def test_apelidos_de_coluna_em_ingles(self):
        produtos = agrupar([
            {"Name": "Tee", "SKU": "T-1", "Price": "99.90", "Stock": "5", "Size": "M"}
        ])
        self.assertEqual(produtos[0].nome, "Tee")
        self.assertEqual(produtos[0].variantes[0].preco, "99.90")
        self.assertEqual(produtos[0].variantes[0].estoque, 5)

    def test_cabecalho_com_acento_e_espaco(self):
        produtos = agrupar([
            {"Nome": "Calça", "Preço": "R$ 349,90", "Descrição": "sarja", "SKU": "X"}
        ])
        self.assertEqual(produtos[0].nome, "Calça")
        self.assertEqual(produtos[0].variantes[0].preco, "349.90")
        self.assertEqual(produtos[0].descricao, "sarja")

    def test_campos_do_produto_completados_por_linha_posterior(self):
        produtos = agrupar([
            {"nome": "Camiseta", "sku": "C-P", "preco": "10", "tamanho": "P"},
            {"nome": "Camiseta", "sku": "C-M", "preco": "10", "tamanho": "M",
             "descricao": "veio depois", "imagens": "b.jpg"},
        ])
        self.assertEqual(produtos[0].descricao, "veio depois")
        self.assertEqual(produtos[0].imagens, ["b.jpg"])

    def test_coluna_livre_vira_atributo(self):
        produtos = agrupar([
            {"nome": "Camiseta", "sku": "C-1", "preco": "10", "atributo_estampa": "Logo"}
        ])
        self.assertEqual(produtos[0].nomes_atributos, ["Estampa"])
        self.assertEqual(produtos[0].variantes[0].atributos, {"Estampa": "Logo"})

    def test_linhas_vazias_sao_ignoradas(self):
        produtos = agrupar([
            {"nome": "Camiseta", "sku": "C-1", "preco": "10"},
            {"nome": "", "sku": "", "preco": ""},
        ])
        self.assertEqual(len(produtos), 1)

    def test_grupo_separa_produtos_de_mesmo_nome(self):
        produtos = agrupar([
            {"grupo": "A", "nome": "Camiseta", "sku": "1", "preco": "10"},
            {"grupo": "B", "nome": "Camiseta", "sku": "2", "preco": "10"},
        ])
        self.assertEqual(len(produtos), 2)


class TestArquivos(unittest.TestCase):
    def test_le_csv_com_ponto_e_virgula(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "p.csv"
            caminho.write_text(
                "nome;sku;preco;tamanho\nCamiseta;C-1;199,90;M\n", encoding="utf-8"
            )
            produtos = carregar(caminho)
        self.assertEqual(produtos[0].variantes[0].preco, "199.90")

    def test_le_json_com_variantes_aninhadas(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "p.json"
            caminho.write_text(
                '[{"nome": "Camiseta", "variantes": '
                '[{"sku": "A", "preco": 10, "tamanho": "P"}, '
                '{"sku": "B", "preco": 10, "tamanho": "M"}]}]',
                encoding="utf-8",
            )
            produtos = carregar(caminho)
        self.assertEqual(len(produtos), 1)
        self.assertEqual(len(produtos[0].variantes), 2)
        self.assertEqual(produtos[0].nomes_atributos, ["Tamanho"])


if __name__ == "__main__":
    unittest.main()
