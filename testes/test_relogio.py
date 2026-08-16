import unittest
from datetime import datetime, timedelta

from agente_drop.relogio import (
    esperar_ate,
    formatar_duracao,
    fuso,
    interpretar_horario,
)


class TestInterpretarHorario(unittest.TestCase):
    def test_formato_relogio(self):
        alvo = interpretar_horario("20:00")
        self.assertEqual((alvo.hour, alvo.minute), (20, 0))

    def test_formato_com_h(self):
        alvo = interpretar_horario("20h")
        self.assertEqual((alvo.hour, alvo.minute), (20, 0))
        self.assertEqual(interpretar_horario("20h30").minute, 30)

    def test_nunca_agenda_no_passado(self):
        agora = datetime.now(fuso())
        alvo = interpretar_horario(f"{agora.hour:02d}:{agora.minute:02d}")
        self.assertGreater(alvo, agora)

    def test_data_completa(self):
        alvo = interpretar_horario("2030-08-10 20:00")
        self.assertEqual((alvo.year, alvo.hour), (2030, 20))

    def test_data_brasileira(self):
        alvo = interpretar_horario("10/08/2030 20:00")
        self.assertEqual((alvo.day, alvo.month, alvo.year), (10, 8, 2030))

    def test_horario_invalido(self):
        with self.assertRaises(ValueError):
            interpretar_horario("qualquer coisa")
        with self.assertRaises(ValueError):
            interpretar_horario("")

    def test_hora_fora_do_intervalo(self):
        with self.assertRaises(ValueError):
            interpretar_horario("99:00")


class TestEsperarAte(unittest.TestCase):
    def test_retorna_na_hora_certa(self):
        agora = datetime.now(fuso())
        alvo = agora + timedelta(seconds=90)
        marcador = {"t": agora}

        def dormir(segundos):
            marcador["t"] = marcador["t"] + timedelta(seconds=segundos)

        esperar_ate(alvo, dormir=dormir, relogio=lambda: marcador["t"], passo=30)
        self.assertGreaterEqual(marcador["t"], alvo)

    def test_horario_ja_passado_retorna_direto(self):
        alvo = datetime.now(fuso()) - timedelta(minutes=1)
        chamadas = []
        esperar_ate(alvo, dormir=lambda s: chamadas.append(s))
        self.assertEqual(chamadas, [])

    def test_avisa_ao_cruzar_marcos(self):
        agora = datetime.now(fuso())
        alvo = agora + timedelta(minutes=5)
        marcador = {"t": agora}
        avisos = []

        def dormir(segundos):
            marcador["t"] = marcador["t"] + timedelta(seconds=segundos)

        esperar_ate(
            alvo,
            dormir=dormir,
            relogio=lambda: marcador["t"],
            aviso=avisos.append,
            passo=30,
        )
        self.assertTrue(avisos)
        # Nao pode virar spam: um aviso por marco, nao um por ciclo.
        self.assertLess(len(avisos), 6)


class TestFormatarDuracao(unittest.TestCase):
    def test_horas(self):
        self.assertEqual(formatar_duracao(7 * 3600 + 30 * 60), "7h30min")

    def test_minutos(self):
        self.assertEqual(formatar_duracao(90), "1min30s")

    def test_segundos(self):
        self.assertEqual(formatar_duracao(9), "9s")

    def test_negativo_vira_zero(self):
        self.assertEqual(formatar_duracao(-5), "0s")


if __name__ == "__main__":
    unittest.main()
