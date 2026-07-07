import os
from datetime import datetime
from loguru import logger


PASTA_LOGS = "logs"


def configurar_logs():
    """
    Configura o loguru para salvar logs em arquivo além do terminal.
    Chame isso UMA vez no início do bot.py.
    """
    os.makedirs(PASTA_LOGS, exist_ok=True)

    nome_log = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    caminho_log = os.path.join(PASTA_LOGS, f"execucao_{nome_log}.log")

    # Remove o handler padrão (terminal) e reconfigura com formato personalizado
    logger.remove()

    # Terminal — colorido e limpo
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        colorize=True,
        level="DEBUG",
    )

    # Arquivo — completo com data, hora e nível
    logger.add(
        sink=caminho_log,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        encoding="utf-8",
    )

    logger.info(f"Log salvo em: {caminho_log}")
    return caminho_log


def salvar_relatorio(resultados: dict, invalidos: list, caminho_log: str):
    """
    Gera um relatório .txt humano e legível de cada execução.
    Salvo na mesma pasta dos logs.
    """
    agora      = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    nome_arq   = os.path.basename(caminho_log).replace(".log", "_relatorio.txt")
    caminho_txt = os.path.join(PASTA_LOGS, nome_arq)

    sucesso  = resultados.get("sucesso", [])
    falha    = resultados.get("falha", [])
    total    = len(sucesso) + len(falha) + len(invalidos)

    linhas = [
        "=" * 56,
        "  BOT DE GERAÇÃO DE NOTAS FISCAIS — RELATÓRIO DE EXECUÇÃO",
        "=" * 56,
        f"  Data/Hora  : {agora}",
        f"  Total CSV  : {total} registro(s)",
        f"  Sucesso    : {len(sucesso)}",
        f"  Falhas     : {len(falha)}",
        f"  Ignorados  : {len(invalidos)} (CSV inválido)",
        "=" * 56,
    ]

    if sucesso:
        linhas.append("\n✅ NOTAS EMITIDAS COM SUCESSO:")
        for r in sucesso:
            linhas.append(f"   → {r['nome']:<30} {r['arquivo']}")

    if falha:
        linhas.append("\n❌ FALHAS NO PROCESSAMENTO:")
        for r in falha:
            linhas.append(f"   → {r['nome']:<30} Erro: {r['erro']}")

    if invalidos:
        linhas.append("\n⚠️  REGISTROS IGNORADOS (ERRO NO CSV):")
        for c in invalidos:
            linhas.append(f"   → Linha {c['linha']:>2}: {c['erros']}")

    linhas.append("\n" + "=" * 56)

    conteudo = "\n".join(linhas)

    with open(caminho_txt, "w", encoding="utf-8") as f:
        f.write(conteudo)

    logger.success(f"Relatório salvo em: {caminho_txt}")
    return caminho_txt