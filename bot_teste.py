from playwright.sync_api import sync_playwright

PORTAL_URL = "http://127.0.0.1:5000"

# Cliente de teste (igual ao CSV)
CLIENTE_TESTE = {
    "nome":      "João Silva",
    "cpf_cnpj":  "123.456.789-00",
    "email":     "joao@email.com",
    "servico":   "Consultoria em TI",
    "valor":     "1500.00",
    "data":      "2026-07-01",
}


def preencher_formulario(page, cliente: dict):
    """Navega até o portal e preenche cada campo do formulário."""

    page.goto(PORTAL_URL)

    # Espera o formulário aparecer na tela antes de interagir
    page.wait_for_selector("#nome_prestador")

    # Preenche cada campo pelo ID do input (o # é seletor CSS de ID)
    page.fill("#nome_prestador", cliente["nome"])
    page.fill("#cpf_cnpj",       str(cliente["cpf_cnpj"]))
    page.fill("#email",          cliente["email"])
    page.fill("#servico",        cliente["servico"])
    page.fill("#valor",          str(cliente["valor"]))
    page.fill("#data",           cliente["data"])

    # Clica no botão emitir
    page.click("#btn-emitir")

    # Aguarda a página de resultado carregar completamente
    page.wait_for_load_state("networkidle")


def salvar_pdf(page, caminho: str):
    """Salva a página atual como PDF."""
    page.pdf(
        path=caminho,
        format="A4",
        print_background=True,   # mantém cores e fundos do CSS
        margin={
            "top":    "20px",
            "bottom": "20px",
            "left":   "20px",
            "right":  "20px",
        }
    )


# ─── Execução ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with sync_playwright() as p:

        # ⚠️ headless=True é obrigatório para page.pdf() funcionar
        # Mude para False se quiser ASSISTIR o bot (mas o PDF não vai salvar)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f" Processando: {CLIENTE_TESTE['nome']}...")

        preencher_formulario(page, CLIENTE_TESTE)

        nome_arquivo = CLIENTE_TESTE["nome"].replace(" ", "_")
        caminho_pdf = f"notas/NF_{nome_arquivo}.pdf"

        salvar_pdf(page, caminho_pdf)
        print(f" PDF salvo em: {caminho_pdf}")

        browser.close()