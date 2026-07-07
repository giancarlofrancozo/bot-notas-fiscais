from flask import Flask, request, render_template_string, make_response
from datetime import datetime
import io

app = Flask(__name__)

# ─── HTML do portal ───────────────────────────────────────────────────────────

TEMPLATE_FORMULARIO = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Portal de Emissão de NFS-e — Maringá</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 30px; }
    .container { max-width: 600px; margin: 0 auto; background: white;
                 padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    h2 { color: #1a3c6e; border-bottom: 2px solid #1a3c6e; padding-bottom: 10px; }
    label { display: block; margin-top: 16px; font-weight: bold; color: #333; }
    input, select, textarea {
      width: 100%; padding: 10px; margin-top: 6px; border: 1px solid #ccc;
      border-radius: 4px; box-sizing: border-box; font-size: 14px;
    }
    button {
      margin-top: 24px; width: 100%; padding: 14px;
      background: #1a3c6e; color: white; border: none;
      border-radius: 4px; font-size: 16px; cursor: pointer;
    }
    button:hover { background: #0f2548; }
    .badge { background: #e8f4fd; color: #1a3c6e; padding: 4px 10px;
             border-radius: 12px; font-size: 12px; margin-left: 8px; }
  </style>
</head>
<body>
  <div class="container">
    <h2> Emissão de NFS-e <span class="badge">Prefeitura Municipal</span></h2>

    <form method="POST" action="/emitir">

      <label for="nome_prestador">Nome / Razão Social do Prestador</label>
      <input type="text" id="nome_prestador" name="nome_prestador"
             placeholder="Ex: João Silva" required>

      <label for="cpf_cnpj">CPF / CNPJ do Prestador</label>
      <input type="text" id="cpf_cnpj" name="cpf_cnpj"
             placeholder="Ex: 123.456.789-00" required>

      <label for="email">E-mail do Prestador</label>
      <input type="email" id="email" name="email"
             placeholder="Ex: joao@email.com" required>

      <label for="servico">Descrição do Serviço</label>
      <input type="text" id="servico" name="servico"
             placeholder="Ex: Consultoria em TI" required>

      <label for="valor">Valor do Serviço (R$)</label>
      <input type="number" id="valor" name="valor"
             step="0.01" min="0.01" placeholder="Ex: 1500.00" required>

      <label for="data">Data de Competência</label>
      <input type="date" id="data" name="data" required>

      <button type="submit" id="btn-emitir"> Emitir Nota Fiscal</button>

    </form>
  </div>
</body>
</html>
"""

# ─── HTML da NF gerada (usada para gerar o PDF) ───────────────────────────────

TEMPLATE_NOTA = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>NFS-e #{numero}</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 40px; color: #222; }}
    .header {{ text-align: center; border-bottom: 3px solid #1a3c6e; padding-bottom: 20px; }}
    .header h1 {{ color: #1a3c6e; margin: 0; font-size: 24px; }}
    .header p {{ color: #666; margin: 4px 0; }}
    .numero {{ text-align: center; font-size: 32px; font-weight: bold;
               color: #1a3c6e; margin: 20px 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    td {{ padding: 12px 16px; border-bottom: 1px solid #eee; }}
    td:first-child {{ font-weight: bold; color: #555; width: 35%; }}
    .valor {{ font-size: 20px; font-weight: bold; color: #1a6e3c; }}
    .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>🏛️ PREFEITURA MUNICIPAL DE MARINGÁ</h1>
    <p>Nota Fiscal de Serviços Eletrônica — NFS-e</p>
  </div>

  <div class="numero">NFS-e Nº {numero}</div>

  <table>
    <tr><td>Prestador</td><td>{nome}</td></tr>
    <tr><td>CPF / CNPJ</td><td>{cpf_cnpj}</td></tr>
    <tr><td>E-mail</td><td>{email}</td></tr>
    <tr><td>Serviço Prestado</td><td>{servico}</td></tr>
    <tr><td>Data de Competência</td><td>{data}</td></tr>
    <tr><td>Valor</td><td class="valor">R$ {valor}</td></tr>
    <tr><td>Data de Emissão</td><td>{emissao}</td></tr>
  </table>

  <div class="footer">
    Documento gerado automaticamente pelo sistema de emissão NFS-e.<br>
    Autenticidade verificável no portal da Prefeitura.
  </div>
</body>
</html>
"""

# ─── Rotas ────────────────────────────────────────────────────────────────────

@app.route("/")
def formulario():
    return render_template_string(TEMPLATE_FORMULARIO)


@app.route("/emitir", methods=["POST"])
def emitir():
    dados = {
        "numero":    str(datetime.now().strftime("%Y%m%d%H%M%S")),
        "nome":      request.form.get("nome_prestador"),
        "cpf_cnpj":  request.form.get("cpf_cnpj"),
        "email":     request.form.get("email"),
        "servico":   request.form.get("servico"),
        "valor":     f"{float(request.form.get('valor', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "data":      request.form.get("data"),
        "emissao":   datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
    }

    html_nota = TEMPLATE_NOTA.format(**dados)

    # Devolve o HTML com header para o Playwright salvar como PDF
    response = make_response(html_nota)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["X-Nota-Numero"] = dados["numero"]
    return response


if __name__ == "__main__":
    app.run(port=5000, debug=True)