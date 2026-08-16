import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agente_drop.catalogo import Produto, Variante
from agente_drop.validacao import ERRO, tem_erro, validar
from testes.apoio import produto_teste


def campos_com_erro(problemas):
    return {p.campo for p in problemas if p.nivel == ERRO}


class TestValidacao(unittest.TestCase):
    def test_produto_bom_nao_gera_erro(self):
        problemas = validar([produto_teste(imagens=["https://exemplo.com/a.jpg"])])
        self.assertFalse(tem_erro(problemas))

    def test_catalogo_vazio_e_erro(self):
        self.assertTrue(tem_erro(validar([])))

    def test_variante_sem_preco(self):
        produto = produto_teste()
        produto.variantes[0].preco = None
        self.assertIn("preco", campos_com_erro(validar([produto])))

    def test_preco_zero(self):
        produto = produto_teste()
        produto.variantes[0].preco = "0.00"
        self.assertIn("preco", campos_com_erro(validar([produto])))

    def test_promocional_maior_que_preco(self):
        produto = produto_teste()
        produto.variantes[0].preco_promocional = "299.90"
        self.assertIn("preco_promocional", campos_com_erro(validar([produto])))

    def test_promocional_valido_passa(self):
        produto = produto_teste()
        produto.variantes[0].preco_promocional = "149.90"
        self.assertNotIn("preco_promocional", campos_com_erro(validar([produto])))

    def test_sku_repetido_entre_produtos(self):
        problemas = validar([produto_teste(sku="IGUAL"), produto_teste(nome="Outro", sku="IGUAL")])
        self.assertIn("sku", campos_com_erro(problemas))

    def test_estoque_negativo(self):
        produto = produto_teste()
        produto.variantes[0].estoque = -1
        self.assertIn("estoque", campos_com_erro(validar([produto])))

    def test_estoque_zero_e_so_aviso(self):
        produto = produto_teste()
        produto.variantes[0].estoque = 0
        problemas = validar([produto])
        self.assertFalse(tem_erro(problemas))
        self.assertTrue(any(p.campo == "estoque" for p in problemas))

    def test_variante_sem_valor_de_atributo(self):
        produto = Produto(
            grupo="g", nome="Camiseta",
            variantes=[
                Variante(sku="A", preco="10", atributos={"Tamanho": "P"}),
                Variante(sku="B", preco="10", atributos={}),  # falta o Tamanho
            ],
        )
        self.assertIn("atributos", campos_com_erro(validar([produto])))

    def test_combinacao_de_atributo_repetida(self):
        produto = Produto(
            grupo="g", nome="Camiseta",
            variantes=[
                Variante(sku="A", preco="10", atributos={"Tamanho": "M"}),
                Variante(sku="B", preco="10", atributos={"Tamanho": "M"}),
            ],
        )
        self.assertIn("atributos", campos_com_erro(validar([produto])))

    def test_mais_de_tres_atributos(self):
        produto = Produto(
            grupo="g", nome="Camiseta",
            variantes=[
                Variante(sku="A", preco="10", atributos={
                    "Tamanho": "M", "Cor": "Preto", "Estampa": "Logo", "Lavagem": "Stone"
                })
            ],
        )
        self.assertIn("atributos", campos_com_erro(validar([produto])))

    def test_imagem_local_inexistente_e_erro(self):
        produto = produto_teste(imagens=["imagens/sumida.jpg"])
        self.assertIn("imagens", campos_com_erro(validar([produto])))

    def test_imagem_local_existente_passa(self):
        with TemporaryDirectory() as pasta:
            (Path(pasta) / "foto.jpg").write_bytes(b"x")
            produto = produto_teste(imagens=["foto.jpg"])
            problemas = validar([produto], raiz_imagens=pasta)
        self.assertNotIn("imagens", campos_com_erro(problemas))

    def test_url_de_imagem_nao_e_checada_no_disco(self):
        produto = produto_teste(imagens=["https://exemplo.com/a.jpg"])
        self.assertNotIn("imagens", campos_com_erro(validar([produto])))

    def test_sem_foto_e_aviso_nao_erro(self):
        problemas = validar([produto_teste(imagens=[])])
        self.assertFalse(tem_erro(problemas))
        self.assertTrue(any(p.campo == "imagens" for p in problemas))

    def test_handle_repetido(self):
        problemas = validar([
            produto_teste(nome="A", sku="1", handle="mesmo"),
            produto_teste(nome="B", sku="2", handle="mesmo"),
        ])
        self.assertIn("handle", campos_com_erro(problemas))

    def test_problema_aponta_a_linha_da_planilha(self):
        produto = produto_teste()
        produto.variantes[0].preco = None
        produto.variantes[0].linha = 42
        problema = next(p for p in validar([produto]) if p.campo == "preco")
        self.assertEqual(problema.linha, 42)


if __name__ == "__main__":
    unittest.main()
