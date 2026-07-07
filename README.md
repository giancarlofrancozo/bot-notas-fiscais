<div align="center">
  <h1> Bot de Geração de NFS-e</h1>
  <p><strong>Automação de emissão de Notas Fiscais de Serviços Eletrônicas</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/Playwright-✓-green?style=flat&logo=playwright" alt="Playwright">
    <img src="https://img.shields.io/badge/Flask-✓-black?style=flat&logo=flask" alt="Flask">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

---

##  Sobre o Projeto

Este bot automatiza o processo de emissão de **Notas Fiscais de Serviços Eletrônicas (NFS-e)**. Ele lê dados de clientes de um arquivo CSV, preenche formulários automaticamente em um portal web, gera os PDFs das notas fiscais e organiza tudo em pastas separadas por cliente.

###  Fluxo de Funcionamento

```
CSV de Clientes → Leitor (Pandas) → Playwright (navegador headless)
                                        ↓
                                 Portal Flask (localhost:5000)
                                        ↓
                              Preenchimento do formulário NFS-e
                                        ↓
                                 Captura do PDF da nota gerada
                                        ↓
                          Organizador → Pastas por cliente
                                        ↓
                              Relatório detalhado de execução
```

##  Estrutura do Projeto

```
bot-notas-fiscais/
├── bot.py              #  Bot principal — automação com Playwright
├── app_gui.py          #  Interface gráfica (CustomTkinter)
├── leitor.py           # Leitura e validação de arquivos CSV
├── organizador.py      #  Organização de PDFs em pastas por cliente
├── relatorio.py        #  Geração de relatórios de execução
├── servidor/
│   ├── app.py          #  Servidor Flask simulando portal de prefeitura
│   └── __init__.py
├── dados/
│   └── clientes.csv    #  Base de dados dos clientes
├── logs/               #  Logs e relatórios gerados
├── notas/              #  PDFs das notas fiscais geradas
├── requirements.txt    #  Dependências do projeto
└── README.md           #  Este arquivo
```

##  Como Usar

### 1. Instalação

```bash
# Clone o repositório
git clone https://github.com/giancarlofrancozo/bot-notas-fiscais.git
cd bot-notas-fiscais

# Instale as dependências
pip install -r requirements.txt

# Instale os navegadores do Playwright
playwright install chromium
```

### 2. Preparar o CSV

Edite o arquivo `dados/clientes.csv` com os dados dos clientes. As colunas obrigatórias são:

| Coluna     | Descrição                    | Exemplo                  |
|------------|------------------------------|--------------------------|
| `nome`     | Nome / Razão Social          | João Silva               |
| `cpf_cnpj` | CPF ou CNPJ do prestador     | 123.456.789-00           |
| `email`    | E-mail do prestador          | joao@email.com           |
| `servico`  | Descrição do serviço         | Consultoria em TI        |
| `valor`    | Valor do serviço (R$)        | 1500.00                  |
| `data`     | Data de competência          | 2026-07-06               |

### 3. Executar

####  Modo Gráfico (recomendado)

```bash
python app_gui.py
```

A interface gráfica permite:
- Selecionar/recarregar arquivo CSV
- Visualizar clientes em tabela
- Iniciar/parar servidor Flask integrado
- Acompanhar o progresso em tempo real
- Visualizar logs detalhados

####  Modo Terminal

```bash
# Inicie o servidor Flask em um terminal
python servidor/app.py

# Em outro terminal, execute o bot
python bot.py
```

##  Funcionalidades

-  **Leitura inteligente de CSV** — validação linha a linha com detecção de erros
-  **Automação headless** — navegador Chromium rodando em segundo plano
-  **Geração de PDF** — captura fiel da nota fiscal gerada
-  **Organização automática** — pastas separadas por cliente
-  **Relatório detalhado** — resumo de sucessos, falhas e erros
-  **Interface gráfica** — acompanhamento visual do progresso
-  **Logs completos** — arquivos de log com data/hora para auditoria
-  **Suporte a cancelamento** — interrompa o processamento a qualquer momento

##  Dependências

| Pacote            | Versão | Finalidade                    |
|-------------------|--------|-------------------------------|
| `playwright`      | -      | Automação do navegador        |
| `flask`           | -      | Servidor web local            |
| `pandas`          | -      | Leitura e validação de CSV    |
| `customtkinter`   | -      | Interface gráfica moderna     |
| `loguru`          | -      | Logging estruturado           |
| `python-dotenv`   | -      | Configuração por variáveis    |

##  Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">
  <p>Desenvolvido por <a href="https://github.com/giancarlofrancozo">@giancarlofrancozo</a></p>
</div>
