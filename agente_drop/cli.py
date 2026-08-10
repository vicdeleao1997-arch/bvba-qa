"""Linha de comando do agente de drop.

    python -m agente_drop validar        # so o arquivo, sem tocar na loja
    python -m agente_drop conferir       # testa credenciais e mostra a loja
    python -m agente_drop plano          # o que seria feito (nao escreve nada)
    python -m agente_drop subir --aplicar
    python -m agente_drop status
    python -m agente_drop publicar --as 20:00
    python -m agente_drop despublicar --sim
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, relatorio as mod_relatorio
from .agente import ATUALIZAR, CRIAR, PULAR, AgenteDrop
from .catalogo import ErroCatalogo, carregar
from .config import Config, ErroConfig, carregar_config
from .estado import Estado
from .nuvemshop import ClienteNuvemshop, ErroNuvemshop
from .relogio import agora, esperar_ate, formatar_duracao, interpretar_horario
from .validacao import ERRO, resumir, tem_erro, validar

CATALOGO_PADRAO = "catalogo/produtos.csv"


def log(mensagem: str = "") -> None:
    print(mensagem, flush=True)


# --------------------------------------------------------------- helpers --


def _config(args) -> Config:
    return carregar_config(args.env)


def _cliente(config: Config) -> ClienteNuvemshop:
    return ClienteNuvemshop(config)


def _carregar_catalogo(args):
    produtos = carregar(args.catalogo)
    problemas = validar(produtos, raiz_imagens=args.imagens)
    return produtos, problemas


def _mostrar_problemas(problemas) -> None:
    erros, avisos = resumir(problemas)
    for problema in problemas:
        if problema.nivel == ERRO:
            log(f"  {problema}")
    for problema in problemas:
        if problema.nivel != ERRO:
            log(f"  {problema}")
    log()
    log(f"  {erros} erro(s), {avisos} aviso(s).")


# -------------------------------------------------------------- comandos --


def cmd_validar(args) -> int:
    produtos, problemas = _carregar_catalogo(args)
    variantes = sum(len(p.variantes) for p in produtos)
    log(f"Catalogo: {args.catalogo}")
    log(f"  {len(produtos)} produto(s), {variantes} variante(s).")
    log()

    if not problemas:
        log("  Nenhum problema encontrado. Pode subir.")
        return 0

    _mostrar_problemas(problemas)
    if tem_erro(problemas):
        log()
        log("  Corrija os erros antes de subir. Avisos nao bloqueiam.")
        return 1
    return 0


def cmd_conferir(args) -> int:
    config = _config(args)
    cliente = _cliente(config)
    log(f"Conferindo acesso... ({config.resumo()})")
    try:
        loja = cliente.loja()
    except ErroNuvemshop as erro:
        log(f"  FALHOU: {erro.descricao()}")
        if erro.status == 401:
            log("  -> 401: confira NUVEMSHOP_ACCESS_TOKEN e o store id.")
        elif erro.status == 404:
            log("  -> 404: store id provavelmente errado.")
        elif erro.status == 400:
            log("  -> 400: costuma ser User-Agent sem email de contato.")
        return 1

    nome = loja.get("name")
    if isinstance(nome, dict):
        nome = nome.get(config.idioma) or next(iter(nome.values()), "")
    log(f"  OK: conectado em \"{nome}\" (id {loja.get('id')}).")
    log(f"  Moeda: {loja.get('main_currency')} | Idioma: {loja.get('main_language')}")
    return 0


def cmd_plano(args) -> int:
    produtos, problemas = _carregar_catalogo(args)
    if tem_erro(problemas):
        log("Catalogo com erros — o plano nao roda ate corrigir:")
        _mostrar_problemas(problemas)
        return 1

    config = _config(args)
    estado = Estado.carregar(args.estado)
    agente = AgenteDrop(_cliente(config), config, estado, raiz_imagens=args.imagens, log=log)
    acoes = agente.planejar(produtos, forcar=args.forcar)

    simbolos = {CRIAR: "+", ATUALIZAR: "~", PULAR: "="}
    log(f"Plano para {len(acoes)} produto(s):")
    log()
    for acao in acoes:
        variantes = len(acao.produto.variantes)
        fotos = len(acao.produto.imagens)
        log(
            f"  {simbolos[acao.tipo]} {acao.rotulo} "
            f"({variantes} var, {fotos} foto(s)) — {acao.motivo}"
        )

    contagem = {tipo: sum(1 for a in acoes if a.tipo == tipo) for tipo in simbolos}
    log()
    log(
        f"  criar: {contagem[CRIAR]} | atualizar: {contagem[ATUALIZAR]} "
        f"| sem mudanca: {contagem[PULAR]}"
    )
    log()
    log("  Nada foi escrito na loja. Para aplicar: python -m agente_drop subir --aplicar")
    return 0


def cmd_subir(args) -> int:
    produtos, problemas = _carregar_catalogo(args)
    if tem_erro(problemas):
        log("Catalogo com erros — nada foi enviado:")
        _mostrar_problemas(problemas)
        return 1

    if not args.aplicar:
        log("Modo simulacao (sem --aplicar). Mostrando o plano:")
        log()
        return cmd_plano(args)

    config = _config(args)
    estado = Estado.carregar(args.estado)
    estado.loja = config.store_id
    cliente = _cliente(config)
    agente = AgenteDrop(cliente, config, estado, raiz_imagens=args.imagens, log=log)

    acoes = agente.planejar(produtos, forcar=args.forcar)
    a_fazer = [a for a in acoes if a.tipo != PULAR]
    log(f"Subindo {len(a_fazer)} produto(s) como RASCUNHO (nao publicado)...")
    log()

    relatorio = agente.executar(acoes)

    log()
    log(
        f"Feito: {len(relatorio.criados)} criado(s), "
        f"{len(relatorio.atualizados)} atualizado(s), "
        f"{len(relatorio.pulados)} sem mudanca, "
        f"{len(relatorio.falhas)} falha(s)."
    )

    caminho_md, _ = mod_relatorio.salvar(relatorio, estado, config, problemas, args.relatorios)
    log(f"Relatorio: {caminho_md}")
    log()
    log("Nenhum produto esta visivel na loja ainda.")
    log("Publicacao: python -m agente_drop publicar --as 20:00")

    return 1 if relatorio.falhas else 0


def cmd_status(args) -> int:
    config = _config(args)
    estado = Estado.carregar(args.estado)
    if not estado.itens:
        log("Nenhum produto registrado ainda. Rode: python -m agente_drop subir --aplicar")
        return 0

    cliente = _cliente(config)
    log(f"{len(estado.itens)} produto(s) no estado do drop. Conferindo na loja...")
    log()

    publicados = 0
    rascunhos = 0
    sumidos = 0
    for item in estado.itens.values():
        try:
            remoto = cliente.obter_produto(item.produto_id)
        except ErroNuvemshop as erro:
            sumidos += 1
            log(f"  ? {item.nome} (#{item.produto_id}): {erro}")
            continue
        no_ar = bool(remoto.get("published"))
        variantes = len(remoto.get("variants") or [])
        fotos = len(remoto.get("images") or [])
        if no_ar:
            publicados += 1
        else:
            rascunhos += 1
        log(
            f"  {'PUBLICADO' if no_ar else 'rascunho '} {item.nome} "
            f"(#{item.produto_id}) — {variantes} var, {fotos} foto(s)"
        )

    log()
    log(f"  rascunho: {rascunhos} | publicado: {publicados} | inacessivel: {sumidos}")
    return 0


def cmd_publicar(args) -> int:
    config = _config(args)
    estado = Estado.carregar(args.estado)
    if not estado.itens:
        log("Nada para publicar: o estado do drop esta vazio.")
        return 1

    if args.as_horario and not args.agora:
        alvo = interpretar_horario(args.as_horario, config.fuso)
        restante = (alvo - agora(config.fuso)).total_seconds()
        log(f"{len(estado.itens)} produto(s) prontos.")

        if restante < 0:
            # Acontece quando o horario vem com data explicita e o processo
            # so comecou depois da hora (runner de CI atrasado, maquina que
            # demorou a acordar). Publicar 5 minutos tarde e o certo;
            # publicar 6 horas tarde, quase nunca.
            atraso = -restante
            if atraso > args.tolerancia * 60:
                log(f"O horario {alvo:%d/%m/%Y %H:%M} passou ha "
                    f"{formatar_duracao(atraso)}, acima da tolerancia de "
                    f"{args.tolerancia} min.")
                log("Nada foi publicado. Se ainda quiser publicar, rode com --agora.")
                return 1
            log(f"Horario alvo passou ha {formatar_duracao(atraso)} "
                f"(dentro da tolerancia de {args.tolerancia} min). Publicando agora.")
        else:
            log(f"Publicacao agendada para {alvo:%d/%m/%Y %H:%M:%S %Z} "
                f"(em {formatar_duracao(restante)}).")
            log("Deixe este processo rodando. Ctrl+C cancela sem publicar.")
            log()
            try:
                esperar_ate(alvo, aviso=lambda m: log(f"  ... {m}"))
            except KeyboardInterrupt:
                log()
                log("Cancelado. Nada foi publicado.")
                return 130

    log(f"Publicando {len(estado.itens)} produto(s)...")
    agente = AgenteDrop(_cliente(config), config, estado, raiz_imagens=args.imagens, log=log)
    resultados = agente.publicar(publicado=True)

    falhas = [r for r in resultados if not r[1]]
    log()
    log(f"Publicados: {len(resultados) - len(falhas)}/{len(resultados)}.")
    if falhas:
        log("Falhas:")
        for produto_id, _, mensagem in falhas:
            log(f"  - #{produto_id} {mensagem}")
        return 1

    log("Drop no ar.")
    return 0


def cmd_despublicar(args) -> int:
    config = _config(args)
    estado = Estado.carregar(args.estado)
    if not estado.itens:
        log("Nada para despublicar.")
        return 1

    if not args.sim:
        log(f"Isso vai tirar {len(estado.itens)} produto(s) do ar.")
        log("Confirme com: python -m agente_drop despublicar --sim")
        return 1

    log(f"Despublicando {len(estado.itens)} produto(s)...")
    agente = AgenteDrop(_cliente(config), config, estado, raiz_imagens=args.imagens, log=log)
    resultados = agente.publicar(publicado=False)
    falhas = [r for r in resultados if not r[1]]
    log()
    log(f"Fora do ar: {len(resultados) - len(falhas)}/{len(resultados)}.")
    return 1 if falhas else 0


# ------------------------------------------------------------- argumentos --


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agente_drop",
        description="Agente autonomo de drop da BVBA na Nuvemshop.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version=f"agente_drop {__version__}")

    comuns = argparse.ArgumentParser(add_help=False)
    comuns.add_argument("--catalogo", default=CATALOGO_PADRAO, help="CSV ou JSON dos produtos")
    comuns.add_argument("--estado", default=".estado_drop.json", help="arquivo de estado do drop")
    comuns.add_argument("--imagens", default=".", help="pasta base das imagens locais")
    comuns.add_argument("--env", default=".env", help="arquivo .env com as credenciais")
    comuns.add_argument("--relatorios", default="relatorios", help="pasta dos relatorios")

    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("validar", parents=[comuns], help="confere o catalogo sem tocar na loja")
    p.set_defaults(func=cmd_validar)

    p = sub.add_parser("conferir", parents=[comuns], help="testa as credenciais da API")
    p.set_defaults(func=cmd_conferir)

    p = sub.add_parser("plano", parents=[comuns], help="mostra o que seria feito")
    p.add_argument("--forcar", action="store_true", help="reenviar mesmo sem mudanca")
    p.set_defaults(func=cmd_plano)

    p = sub.add_parser("subir", parents=[comuns], help="cria/atualiza os produtos como rascunho")
    p.add_argument("--aplicar", action="store_true", help="escreve de fato na loja")
    p.add_argument("--forcar", action="store_true", help="reenviar mesmo sem mudanca")
    p.set_defaults(func=cmd_subir)

    p = sub.add_parser("status", parents=[comuns], help="compara o estado local com a loja")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("publicar", parents=[comuns], help="poe o drop no ar")
    p.add_argument("--as", dest="as_horario", default=None, help='horario, ex.: "20:00"')
    p.add_argument("--agora", action="store_true", help="publica imediatamente")
    p.add_argument(
        "--tolerancia",
        type=int,
        default=120,
        help="minutos de atraso ainda aceitaveis para publicar (padrao: 120)",
    )
    p.set_defaults(func=cmd_publicar)

    p = sub.add_parser("despublicar", parents=[comuns], help="tira o drop do ar (rollback)")
    p.add_argument("--sim", action="store_true", help="confirma a operacao")
    p.set_defaults(func=cmd_despublicar)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)

    if getattr(args, "comando", None) == "publicar" and not args.as_horario and not args.agora:
        log("Escolha --as HH:MM (agendado) ou --agora (imediato).")
        return 2

    try:
        return args.func(args)
    except (ErroConfig, ErroCatalogo, ValueError) as erro:
        log(f"Erro: {erro}")
        return 2
    except ErroNuvemshop as erro:
        log(f"Erro na API da Nuvemshop: {erro.descricao()}")
        return 3
    except KeyboardInterrupt:
        log()
        log("Interrompido.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
