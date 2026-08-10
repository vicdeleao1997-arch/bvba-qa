"""Testes do preenchedor de pendencias.

Ele escreve direto no catalogo do drop, entao errar aqui e caro: preco na
variante errada, foto na peca errada.
"""

import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ferramentas.preencher import (
    ErroPendencias,
    aplicar,
    ler_pendencias,
    parse_estoque,
    parse_fotos,
    parse_preco,
)

COLUNAS = ["grupo", "nome", "descricao", "sku", "preco", "estoque",
           "tamanho", "cor", "peso", "marca", "categorias", "tags", "imagens"]
TAMANHOS = ["P", "M", "G", "GG", "XGG"]


def catalogo_de_teste(pasta, refs=("MLT-001", "CMS-004")):
    caminho = Path(pasta) / "produtos.csv"
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        for ref in refs:
            for tam in TAMANHOS:
                w.writerow({c: "" for c in COLUNAS} | {
                    "grupo": ref, "nome": ref, "sku": f"BVBA-{ref}-{tam}", "tamanho": tam,
                })
    return caminho


def ler(caminho):
    with Path(caminho).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class TestParsePreco(unittest.TestCase):
    def test_formato_brasileiro(self):
        self.assertEqual(parse_preco("R$ 1.299,90"), "1299.90")
        self.assertEqual(parse_preco("399,90"), "399.90")
        self.assertEqual(parse_preco("399.90"), "399.90")

    def test_vazio(self):
        self.assertEqual(parse_preco(""), "")
        self.assertEqual(parse_preco("   "), "")

    def test_invalido(self):
        with self.assertRaises(ErroPendencias):
            parse_preco("combinar")
        with self.assertRaises(ErroPendencias):
            parse_preco("0")
        with self.assertRaises(ErroPendencias):
            parse_preco("-10")


class TestParseEstoque(unittest.TestCase):
    def test_um_valor_vale_para_todos(self):
        self.assertEqual(parse_estoque("12"), ["12"] * 5)

    def test_um_por_tamanho(self):
        self.assertEqual(parse_estoque("10,15,15,10,5"), ["10", "15", "15", "10", "5"])

    def test_vazio(self):
        self.assertEqual(parse_estoque(""), [""] * 5)

    def test_quantidade_errada_de_valores(self):
        with self.assertRaises(ErroPendencias):
            parse_estoque("10,15,15")

    def test_nao_numerico(self):
        with self.assertRaises(ErroPendencias):
            parse_estoque("muitos")


class TestParseFotos(unittest.TestCase):
    def test_faixa(self):
        self.assertEqual(parse_fotos("1-5"), [1, 2, 3, 4, 5])

    def test_faixa_e_solto(self):
        self.assertEqual(parse_fotos("1-3, 10, 14"), [1, 2, 3, 10, 14])

    def test_preserva_a_ordem_escrita(self):
        """A primeira da lista vira a capa, entao a ordem importa."""
        self.assertEqual(parse_fotos("7, 1-2"), [7, 1, 2])

    def test_nao_repete(self):
        self.assertEqual(parse_fotos("1-3, 2"), [1, 2, 3])

    def test_vazio(self):
        self.assertEqual(parse_fotos(""), [])

    def test_faixa_invertida(self):
        with self.assertRaises(ErroPendencias):
            parse_fotos("10-2")

    def test_lixo(self):
        with self.assertRaises(ErroPendencias):
            parse_fotos("primeira foto")


class TestLerPendencias(unittest.TestCase):
    def test_ignora_comentario_e_linha_vazia(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "p.txt"
            caminho.write_text(
                "# comentario\n\nMLT-001 | 399,90 | 10 | 1-3\n", encoding="utf-8"
            )
            pendencias = ler_pendencias(caminho)
        self.assertEqual(list(pendencias), ["MLT-001"])
        self.assertEqual(pendencias["MLT-001"]["preco"], "399.90")

    def test_campos_vazios_sao_aceitos(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "p.txt"
            caminho.write_text("MLT-001 |  |  |\n", encoding="utf-8")
            pendencias = ler_pendencias(caminho)
        self.assertEqual(pendencias["MLT-001"]["preco"], "")
        self.assertEqual(pendencias["MLT-001"]["fotos"], [])

    def test_erro_aponta_a_linha(self):
        with TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "p.txt"
            caminho.write_text("MLT-001 | 399,90 | 10 | 1-3\nCMS-004 | xis | |\n",
                               encoding="utf-8")
            with self.assertRaises(ErroPendencias) as ctx:
                ler_pendencias(caminho)
        self.assertIn("linha 2", str(ctx.exception))
        self.assertIn("CMS-004", str(ctx.exception))


class TestAplicar(unittest.TestCase):
    def test_preco_vai_para_todas_as_variantes_da_peca(self):
        with TemporaryDirectory() as pasta:
            catalogo = catalogo_de_teste(pasta)
            aplicar(catalogo, {"MLT-001": {"preco": "399.90", "estoque": [""] * 5,
                                           "fotos": []}}, Path(pasta))
            linhas = ler(catalogo)

        mlt = [l for l in linhas if l["grupo"] == "MLT-001"]
        cms = [l for l in linhas if l["grupo"] == "CMS-004"]
        self.assertTrue(all(l["preco"] == "399.90" for l in mlt))
        self.assertTrue(all(l["preco"] == "" for l in cms))

    def test_estoque_casa_com_o_tamanho_certo(self):
        with TemporaryDirectory() as pasta:
            catalogo = catalogo_de_teste(pasta)
            aplicar(catalogo, {"MLT-001": {"preco": "", "fotos": [],
                                           "estoque": ["1", "2", "3", "4", "5"]}},
                    Path(pasta))
            linhas = ler(catalogo)

        por_tamanho = {l["tamanho"]: l["estoque"] for l in linhas if l["grupo"] == "MLT-001"}
        self.assertEqual(por_tamanho, {"P": "1", "M": "2", "G": "3", "GG": "4", "XGG": "5"})

    def test_fotos_so_na_primeira_linha_do_grupo(self):
        with TemporaryDirectory() as pasta:
            catalogo = catalogo_de_teste(pasta)
            aplicar(catalogo, {"MLT-001": {"preco": "", "estoque": [""] * 5,
                                           "fotos": [1, 2]}}, Path(pasta))
            linhas = ler(catalogo)

        mlt = [l for l in linhas if l["grupo"] == "MLT-001"]
        self.assertEqual(mlt[0]["imagens"], "imagens/BVBA_-1.jpg|imagens/BVBA_-2.jpg")
        self.assertTrue(all(l["imagens"] == "" for l in mlt[1:]))

    def test_avisa_quando_a_foto_nao_esta_no_disco(self):
        with TemporaryDirectory() as pasta:
            catalogo = catalogo_de_teste(pasta)
            _, avisos = aplicar(catalogo, {"MLT-001": {"preco": "", "estoque": [""] * 5,
                                                       "fotos": [99]}}, Path(pasta))
        self.assertTrue(any("99" in a for a in avisos))

    def test_ref_desconhecida_vira_aviso_e_nao_quebra(self):
        with TemporaryDirectory() as pasta:
            catalogo = catalogo_de_teste(pasta)
            _, avisos = aplicar(catalogo, {"XXX-999": {"preco": "10.00",
                                                       "estoque": [""] * 5, "fotos": []}},
                                Path(pasta))
        self.assertTrue(any("XXX-999" in a for a in avisos))

    def test_campo_vazio_nao_apaga_o_que_ja_existia(self):
        with TemporaryDirectory() as pasta:
            catalogo = catalogo_de_teste(pasta)
            aplicar(catalogo, {"MLT-001": {"preco": "399.90", "estoque": ["7"] * 5,
                                           "fotos": []}}, Path(pasta))
            aplicar(catalogo, {"MLT-001": {"preco": "", "estoque": [""] * 5,
                                           "fotos": []}}, Path(pasta))
            linhas = ler(catalogo)

        mlt = [l for l in linhas if l["grupo"] == "MLT-001"]
        self.assertEqual(mlt[0]["preco"], "399.90")
        self.assertEqual(mlt[0]["estoque"], "7")

    def test_rodar_duas_vezes_da_o_mesmo_resultado(self):
        with TemporaryDirectory() as pasta:
            catalogo = catalogo_de_teste(pasta)
            dados = {"MLT-001": {"preco": "399.90", "estoque": ["7"] * 5, "fotos": [1]}}
            aplicar(catalogo, dados, Path(pasta))
            primeira = catalogo.read_text(encoding="utf-8")
            alterados, _ = aplicar(catalogo, dados, Path(pasta))
            segunda = catalogo.read_text(encoding="utf-8")

        self.assertEqual(primeira, segunda)
        self.assertEqual(alterados, 0)

    def test_preserva_as_colunas_do_catalogo(self):
        with TemporaryDirectory() as pasta:
            catalogo = catalogo_de_teste(pasta)
            aplicar(catalogo, {"MLT-001": {"preco": "10.00", "estoque": [""] * 5,
                                           "fotos": []}}, Path(pasta))
            with catalogo.open(encoding="utf-8-sig", newline="") as f:
                colunas = csv.DictReader(f).fieldnames

        self.assertEqual(colunas, COLUNAS)


if __name__ == "__main__":
    unittest.main()
