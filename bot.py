from playwright.sync_api import sync_playwright
from leitor import carregar_clientes
from organizador import organizar_pdf, listar_estrutura
from relatorio import configurar_logs, salvar_relatorio
from loguru import logger
import os

PORTAL_URL  = "http://127.0.0.1:5000"
CSV_PATH    = "dados/clientes.csv"
PASTA_NOTAS = "notas"


# ─── Funções do bot ───────────────────────────────────────────────────────────

def preencher_formulario(page, cliente: dict):
    page.goto(PORTAL_URL)
    page.wait_for_selector("#nome_prestador")

    page.fill("#nome_prestador", str(cliente["nome"]))
    page.fill("#cpf_cnpj",       str(cliente["cpf_cnpj"]))
    page.fill("#email",          str(cliente["email"]))
    page.fill("#servico",        str(cliente["servico"]))
    page.fill("#valor",          str(cliente["valor"]))
    page.fill("#data",           str(cliente["data"]))

    page.click("#btn-emitir")
    page.wait_for_load_state("networkidle")


def salvar_pdf(page, caminho: str):
    page.pdf(
        path=caminho,
        format="A4",
        print_background=True,
        margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"}
    )


def montar_caminho_pdf(cliente: dict) -> str:
    nome_limpo = str(cliente["nome"]).replace(" ", "_").replace("/", "-")
    data_limpa = str(cliente["data"]).replace("-", "")
    return os.path.join(PASTA_NOTAS, f"NF_{nome_limpo}_{data_limpa}.pdf")


# ─── Loop principal ───────────────────────────────────────────────────────────

def processar_clientes():
    caminho_log = configurar_logs()  # inicia log em arquivo

    validos, invalidos = carregar_clientes(CSV_PATH)

    if not validos:
        logger.error("Nenhum cliente válido encontrado. Encerrando.")
        return

    logger.info(f"Iniciando processamento de {len(validos)} clientes...")
    if invalidos:
        logger.warning(f"{len(invalidos)} cliente(s) ignorado(s) por erros no CSV.")

    resultados = {"sucesso": [], "falha": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(60000)

        for cliente in validos:
            nome = cliente["nome"]
            logger.info(f"Processando: {nome}")

            try:
                preencher_formulario(page, cliente)

                caminho = montar_caminho_pdf(cliente)
                salvar_pdf(page, caminho)

                caminho = organizar_pdf(nome, caminho)

                logger.success(f"{nome} → {caminho}")
                resultados["sucesso"].append({"nome": nome, "arquivo": caminho})

            except Exception as e:
                logger.error(f"{nome} → Erro: {e}")
                resultados["falha"].append({"nome": nome, "erro": str(e)})

        browser.close()

    # ─── Relatório final ──────────────────────────────────────────────────────
    listar_estrutura()
    caminho_txt = salvar_relatorio(resultados, invalidos, caminho_log)

    print(f"\n Execução concluída!")
    print(f"    Log      → {caminho_log}")
    print(f"    Relatório → {caminho_txt}")


# ─── Entrada ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    processar_clientes()