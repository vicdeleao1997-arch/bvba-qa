"""Relatorio do drop em Markdown e JSON."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .agente import Relatorio
from .config import Config
from .estado import Estado
from .validacao import ERRO, Problema


def _admin(config: Config, produto_id: int) -> str:
    """Link para o produto no painel, se soubermos o endereco do painel.

    O subdominio da loja nao sai do store_id, entao so montamos o link quando
    NUVEMSHOP_ADMIN_URL estiver configurado — melhor sem link do que com um
    link quebrado.
    """
    if not config.admin_url:
        return ""
    return f"{config.admin_url}/products/{produto_id}"


def markdown(
    relatorio: Relatorio,
    estado: Estado,
    config: Config,
    problemas: list[Problema] | None = None,
    momento: datetime | None = None,
) -> str:
    momento = momento or datetime.now()
    linhas: list[str] = [
        "# Relatorio do drop BVBA",
        "",
        f"- Gerado em: {momento:%d/%m/%Y %H:%M:%S}",
        f"- Loja: {config.store_id}",
        f"- Chamadas a API: {relatorio.chamadas_api}",
        "",
        "## Resumo",
        "",
        "| Criados | Atualizados | Sem mudanca | Falhas |",
        "|---:|---:|---:|---:|",
        f"| {len(relatorio.criados)} | {len(relatorio.atualizados)} "
        f"| {len(relatorio.pulados)} | {len(relatorio.falhas)} |",
        "",
    ]

    if relatorio.falhas:
        linhas += ["## Falhas (precisam de atencao antes das 20h)", ""]
        for resultado in relatorio.falhas:
            linhas.append(f"- **{resultado.acao.rotulo}** — {resultado.erro}")
            for falha in resultado.imagens_falhas:
                linhas.append(f"  - imagem: {falha}")
        linhas.append("")

    subiram = relatorio.criados + relatorio.atualizados
    if subiram:
        com_link = bool(config.admin_url)
        cabecalho = "| Produto | ID | Variantes | Fotos |"
        separador = "|---|---:|---:|---:|"
        if com_link:
            cabecalho += " Painel |"
            separador += "---|"
        linhas += ["## Produtos no ar como rascunho", "", cabecalho, separador]

        for resultado in subiram:
            item = estado.por_id(resultado.produto_id or 0)
            linha = (
                f"| {resultado.acao.rotulo} | {resultado.produto_id} "
                f"| {len(resultado.acao.produto.variantes)} "
                f"| {len(item.imagens) if item else resultado.imagens_enviadas} |"
            )
            if com_link:
                linha += f" [abrir]({_admin(config, resultado.produto_id or 0)}) |"
            linhas.append(linha)
        linhas.append("")

    if problemas:
        avisos = [p for p in problemas if p.nivel != ERRO]
        if avisos:
            linhas += ["## Avisos do catalogo", ""]
            linhas += [f"- {p}" for p in avisos]
            linhas.append("")

    linhas += [
        "## Proximo passo",
        "",
        "Tudo acima esta **invisivel na loja** (`published: false`).",
        "Para publicar no horario do lancamento:",
        "",
        "```bash",
        "python -m agente_drop publicar --as 20:00",
        "```",
        "",
        "Para reverter depois de publicado:",
        "",
        "```bash",
        "python -m agente_drop despublicar --sim",
        "```",
        "",
    ]
    return "\n".join(linhas)


def salvar(
    relatorio: Relatorio,
    estado: Estado,
    config: Config,
    problemas: list[Problema] | None = None,
    pasta: Path | str = "relatorios",
) -> tuple[Path, Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")

    caminho_md = pasta / f"drop-{carimbo}.md"
    caminho_md.write_text(markdown(relatorio, estado, config, problemas), encoding="utf-8")

    caminho_json = pasta / f"drop-{carimbo}.json"
    corpo = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "loja": config.store_id,
        "chamadas_api": relatorio.chamadas_api,
        "resumo": {
            "criados": len(relatorio.criados),
            "atualizados": len(relatorio.atualizados),
            "pulados": len(relatorio.pulados),
            "falhas": len(relatorio.falhas),
        },
        "produtos": [
            {
                "nome": r.acao.rotulo,
                "acao": r.acao.tipo,
                "produto_id": r.produto_id,
                "ok": r.ok,
                "imagens_enviadas": r.imagens_enviadas,
                "imagens_falhas": r.imagens_falhas,
                "erro": r.erro,
            }
            for r in relatorio.resultados
        ],
        "problemas": [asdict(p) for p in (problemas or [])],
    }
    caminho_json.write_text(
        json.dumps(corpo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return caminho_md, caminho_json
