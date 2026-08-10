"""Horario do lancamento, sem dependencia externa.

Usa ``zoneinfo`` quando o sistema tem a base de fusos; se nao tiver, cai para
o offset fixo -03:00, que e o horario de Brasilia desde o fim do horario de
verao em 2019.
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from typing import Callable

BRASILIA_FIXO = timezone(timedelta(hours=-3), "BRT")


def fuso(nome: str = "America/Sao_Paulo"):
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(nome)
    except Exception:
        # Sem tzdata instalada (comum em container enxuto).
        return BRASILIA_FIXO


def agora(nome_fuso: str = "America/Sao_Paulo") -> datetime:
    return datetime.now(fuso(nome_fuso))


def interpretar_horario(texto: str, nome_fuso: str = "America/Sao_Paulo") -> datetime:
    """Aceita '20:00', '20h', '2026-08-10 20:00' ou ISO completo.

    Um horario sem data significa "hoje"; se ja passou, significa "amanha",
    para nunca agendar no passado.
    """
    texto = (texto or "").strip().lower()
    if not texto:
        raise ValueError("Horario vazio.")

    tz = fuso(nome_fuso)
    referencia = datetime.now(tz)

    # 20h / 20h30
    curto = re.fullmatch(r"(\d{1,2})h(\d{2})?", texto)
    if curto:
        hora = int(curto.group(1))
        minuto = int(curto.group(2) or 0)
        return _proxima_ocorrencia(referencia, hora, minuto)

    # 20:00 / 20:00:00
    relogio = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", texto)
    if relogio:
        return _proxima_ocorrencia(
            referencia,
            int(relogio.group(1)),
            int(relogio.group(2)),
            int(relogio.group(3) or 0),
        )

    # Data completa
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(texto, formato).replace(tzinfo=tz)
        except ValueError:
            continue

    try:
        parseada = datetime.fromisoformat(texto)
    except ValueError as erro:
        raise ValueError(
            f'Nao entendi o horario "{texto}". Use 20:00, 20h, '
            '"2026-08-10 20:00" ou ISO 8601.'
        ) from erro
    return parseada if parseada.tzinfo else parseada.replace(tzinfo=tz)


def _proxima_ocorrencia(
    referencia: datetime, hora: int, minuto: int, segundo: int = 0
) -> datetime:
    if not 0 <= hora <= 23 or not 0 <= minuto <= 59:
        raise ValueError(f"Horario invalido: {hora:02d}:{minuto:02d}")
    alvo = referencia.replace(hour=hora, minute=minuto, second=segundo, microsecond=0)
    if alvo <= referencia:
        alvo += timedelta(days=1)
    return alvo


def esperar_ate(
    alvo: datetime,
    *,
    dormir: Callable[[float], None] = time.sleep,
    relogio: Callable[[], datetime] | None = None,
    aviso: Callable[[str], None] | None = None,
    passo: float = 30.0,
) -> None:
    """Bloqueia ate o horario alvo, avisando de tempos em tempos."""
    tz = alvo.tzinfo or BRASILIA_FIXO
    ler = relogio or (lambda: datetime.now(tz))

    # Comeca no infinito para o primeiro aviso sair na hora, e depois so
    # avisa ao cruzar cada marco (1h, 30min, 15min, 5min, 1min, 10s).
    proximo_aviso = float("inf")
    while True:
        restante = (alvo - ler()).total_seconds()
        if restante <= 0:
            return
        if aviso and restante <= proximo_aviso:
            aviso(f"faltam {formatar_duracao(restante)} para {alvo:%H:%M:%S}")
            proximo_aviso = _proximo_marco(restante)
        dormir(min(passo, restante))


def _proximo_marco(restante: float) -> float:
    for marco in (3600, 1800, 900, 300, 60, 10):
        if restante > marco:
            return float(marco)
    return 0.0


def formatar_duracao(segundos: float) -> str:
    segundos = int(max(0, segundos))
    horas, resto = divmod(segundos, 3600)
    minutos, segs = divmod(resto, 60)
    if horas:
        return f"{horas}h{minutos:02d}min"
    if minutos:
        return f"{minutos}min{segs:02d}s"
    return f"{segs}s"
