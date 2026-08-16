import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agente_drop.agente import ATUALIZAR, CRIAR, PULAR, AgenteDrop, chave_do_produto
from agente_drop.catalogo import Produto, Variante
from agente_drop.estado import Estado
from agente_drop.nuvemshop import ClienteNuvemshop, Limitador
from testes.apoio import LojaFalsa, config_teste, erro_http, produto_teste


def montar(pasta, loja=None):
    loja = loja or LojaFalsa()
    config = config_teste()
    cliente = ClienteNuvemshop(
        config,
        abrir=loja,
        dormir=lambda _: None,
        limitador=Limitador(dormir=lambda _: None, agora=lambda: 0.0),
    )
    estado = Estado.carregar(Path(pasta) / "estado.json")
    agente = AgenteDrop(cliente, config, estado, raiz_imagens=pasta)
    return agente, loja, estado


class TestChave(unittest.TestCase):
    def test_prefere_sku(self):
        self.assertEqual(chave_do_produto(produto_teste(sku="ABC")), "sku:ABC")

    def test_cai_para_handle_sem_sku(self):
        produto = Produto(grupo="g", nome="Camiseta Nova", variantes=[Variante(preco="10")])
        self.assertEqual(chave_do_produto(produto), "handle:camiseta-nova")


class TestPlano(unittest.TestCase):
    def test_produto_novo_vira_criar(self):
        with TemporaryDirectory() as pasta:
            agente, _, _ = montar(pasta)
            acoes = agente.planejar([produto_teste()])
        self.assertEqual(acoes[0].tipo, CRIAR)

    def test_segunda_rodada_sem_mudanca_vira_pular(self):
        with TemporaryDirectory() as pasta:
            agente, _, _ = montar(pasta)
            produto = produto_teste()
            agente.executar(agente.planejar([produto]))
            acoes = agente.planejar([produto])
        self.assertEqual(acoes[0].tipo, PULAR)

    def test_mudanca_de_preco_vira_atualizar(self):
        with TemporaryDirectory() as pasta:
            agente, _, _ = montar(pasta)
            produto = produto_teste()
            agente.executar(agente.planejar([produto]))
            produto.variantes[0].preco = "249.90"
            acoes = agente.planejar([produto])
        self.assertEqual(acoes[0].tipo, ATUALIZAR)

    def test_forcar_reenvia_mesmo_sem_mudanca(self):
        with TemporaryDirectory() as pasta:
            agente, _, _ = montar(pasta)
            produto = produto_teste()
            agente.executar(agente.planejar([produto]))
            acoes = agente.planejar([produto], forcar=True)
        self.assertEqual(acoes[0].tipo, ATUALIZAR)


class TestExecucao(unittest.TestCase):
    def test_cria_produto_como_rascunho(self):
        with TemporaryDirectory() as pasta:
            agente, loja, _ = montar(pasta)
            relatorio = agente.executar(agente.planejar([produto_teste()]))

        self.assertEqual(len(relatorio.criados), 1)
        criado = next(iter(loja.produtos.values()))
        self.assertIs(criado["published"], False)

    def test_nao_duplica_ao_rodar_duas_vezes(self):
        with TemporaryDirectory() as pasta:
            agente, loja, _ = montar(pasta)
            produto = produto_teste()
            agente.executar(agente.planejar([produto]))
            agente.executar(agente.planejar([produto]))

        self.assertEqual(len(loja.produtos), 1)

    def test_estado_guarda_id_e_variantes(self):
        with TemporaryDirectory() as pasta:
            agente, _, estado = montar(pasta)
            agente.executar(agente.planejar([produto_teste(sku="BVBA-1")]))

        item = estado.obter("sku:BVBA-1")
        self.assertIsNotNone(item)
        self.assertIn("BVBA-1", item.variantes)
        self.assertFalse(item.publicado)

    def test_imagens_sao_enviadas_uma_a_uma(self):
        with TemporaryDirectory() as pasta:
            produto = produto_teste(imagens=[
                "https://exemplo.com/a.jpg",
                "https://exemplo.com/b.jpg",
            ])
            agente, loja, _ = montar(pasta)
            relatorio = agente.executar(agente.planejar([produto]))

        self.assertEqual(relatorio.resultados[0].imagens_enviadas, 2)
        self.assertEqual(sum(1 for c in loja.chamadas if c[1].endswith("/images")), 2)

    def test_imagem_nao_e_reenviada_na_segunda_rodada(self):
        with TemporaryDirectory() as pasta:
            produto = produto_teste(imagens=["https://exemplo.com/a.jpg"])
            agente, loja, _ = montar(pasta)
            agente.executar(agente.planejar([produto]))
            produto.variantes[0].preco = "249.90"  # forca um update
            agente.executar(agente.planejar([produto]))

        self.assertEqual(sum(1 for c in loja.chamadas if c[1].endswith("/images")), 1)

    def test_imagem_quebrada_nao_derruba_o_produto(self):
        with TemporaryDirectory() as pasta:
            produto = produto_teste(imagens=["local-inexistente.jpg"])
            agente, loja, estado = montar(pasta)
            relatorio = agente.executar(agente.planejar([produto]))

        # O produto sobe; so a imagem e reportada como falha.
        self.assertEqual(len(loja.produtos), 1)
        self.assertTrue(relatorio.resultados[0].imagens_falhas)
        self.assertIsNotNone(estado.obter("sku:BVBA-1"))

    def test_falha_em_um_produto_nao_para_os_outros(self):
        loja = LojaFalsa()
        loja.falhar_em["POST products"] = erro_http(422, {"erro": "invalido"})
        with TemporaryDirectory() as pasta:
            agente, _, _ = montar(pasta, loja)
            relatorio = agente.executar(agente.planejar([
                produto_teste(nome="A", sku="A-1"),
                produto_teste(nome="B", sku="B-1"),
            ]))

        self.assertEqual(len(relatorio.falhas), 2)
        self.assertEqual(len(relatorio.resultados), 2)

    def test_atualizacao_mexe_na_variante_certa(self):
        with TemporaryDirectory() as pasta:
            agente, loja, _ = montar(pasta)
            produto = produto_teste()
            agente.executar(agente.planejar([produto]))
            produto.variantes[0].preco = "149.90"
            agente.executar(agente.planejar([produto]))

        variante = next(iter(loja.produtos.values()))["variants"][0]
        self.assertEqual(variante["price"], "149.90")
        self.assertEqual(len(next(iter(loja.produtos.values()))["variants"]), 1)

    def test_variante_nova_e_criada_no_update(self):
        with TemporaryDirectory() as pasta:
            agente, loja, _ = montar(pasta)
            produto = produto_teste()
            agente.executar(agente.planejar([produto]))
            produto.variantes.append(
                Variante(sku="BVBA-2", preco="199.90", estoque=5, atributos={"Tamanho": "G"})
            )
            agente.executar(agente.planejar([produto]))

        self.assertEqual(len(next(iter(loja.produtos.values()))["variants"]), 2)

    def test_update_nao_mexe_na_visibilidade(self):
        """Criar trava published=false; atualizar nao toca no campo.

        Sem isso, corrigir um preco com a loja no ar devolveria o produto
        para rascunho no meio do drop.
        """
        with TemporaryDirectory() as pasta:
            agente, loja, _ = montar(pasta)
            produto = produto_teste()
            agente.executar(agente.planejar([produto]))
            produto_id = next(iter(loja.produtos))
            loja.produtos[produto_id]["published"] = True  # simula o drop no ar

            produto.variantes[0].preco = "149.90"
            agente.executar(agente.planejar([produto]))

        self.assertTrue(loja.produtos[produto_id]["published"])

    def test_estado_e_salvo_em_disco(self):
        with TemporaryDirectory() as pasta:
            agente, _, _ = montar(pasta)
            agente.executar(agente.planejar([produto_teste()]))
            recarregado = Estado.carregar(Path(pasta) / "estado.json")

        self.assertEqual(len(recarregado.itens), 1)


class TestPublicacao(unittest.TestCase):
    def test_publicar_liga_todos_os_produtos(self):
        with TemporaryDirectory() as pasta:
            agente, loja, estado = montar(pasta)
            agente.executar(agente.planejar([
                produto_teste(nome="A", sku="A-1"),
                produto_teste(nome="B", sku="B-1"),
            ]))
            self.assertTrue(all(not p["published"] for p in loja.produtos.values()))

            resultados = agente.publicar(publicado=True)

        self.assertEqual(len(resultados), 2)
        self.assertTrue(all(p["published"] for p in loja.produtos.values()))
        self.assertTrue(all(i.publicado for i in estado.itens.values()))

    def test_despublicar_reverte(self):
        with TemporaryDirectory() as pasta:
            agente, loja, _ = montar(pasta)
            agente.executar(agente.planejar([produto_teste()]))
            agente.publicar(publicado=True)
            agente.publicar(publicado=False)

        self.assertTrue(all(not p["published"] for p in loja.produtos.values()))

    def test_falha_de_publicacao_nao_para_o_resto(self):
        with TemporaryDirectory() as pasta:
            agente, loja, estado = montar(pasta)
            agente.executar(agente.planejar([
                produto_teste(nome="A", sku="A-1"),
                produto_teste(nome="B", sku="B-1"),
            ]))
            primeiro = estado.ids[0]
            loja.falhar_em[f"PUT products/{primeiro}"] = erro_http(500)

            resultados = agente.publicar(publicado=True)

        self.assertEqual(sum(1 for r in resultados if r[1]), 1)
        self.assertEqual(sum(1 for r in resultados if not r[1]), 1)


if __name__ == "__main__":
    unittest.main()
