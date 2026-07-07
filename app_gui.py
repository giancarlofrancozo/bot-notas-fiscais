"""
╔══════════════════════════════════════════════════════════════╗
║  Bot de Geração de NFS-e — Interface Gráfica             ║
║  CustomTkinter + Threading + Playwright                     ║
╚══════════════════════════════════════════════════════════════╝
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ─── Tema ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ─── Constantes ───────────────────────────────────────────────────────────────
PASTA_NOTAS = "notas"
PASTA_LOGS  = "logs"
PORTAL_URL  = "http://127.0.0.1:5000"


def _caminho_recurso(caminho_relativo: str) -> str:
    """
    Resolve caminhos para arquivos empacotados no .exe (PyInstaller --onefile).
    Em modo normal, retorna o path absoluto normal.
    """
    if getattr(sys, "frozen", False):
        return str(Path(sys._MEIPASS) / caminho_relativo)
    return str(Path(caminho_relativo).resolve())


DEFAULT_CSV = _caminho_recurso("dados/clientes.csv")


class Aplicacao:
    """Janela principal da interface gráfica."""

    def __init__(self):
        self.janela = ctk.CTk()
        self.janela.title("Bot de Geração de NFS-e")
        self.janela.geometry("960x720")
        self.janela.minsize(860, 600)

        # ─── Estado interno ──────────────────────────────────────────────
        self.csv_path      = ctk.StringVar(value=DEFAULT_CSV)
        self.status_text   = ctk.StringVar(value="Pronto — selecione um CSV e clique em Processar")
        self.progresso_var = ctk.DoubleVar(value=0.0)

        self.total_clientes  = 0
        self.invalidos       = []
        self.caminho_log     = None

        self.processando     = False
        self.cancelar        = False
        self.thread_bot      = None
        self.thread_servidor = None
        self.servidor_rodando= False
        self.fila_mensagens  = queue.Queue()

        # Controle de processamento agendado apos servidor subir
        self._processar_apos_servidor = False
        self._caminho_pendente = None

        # ─── Montagem da interface ──────────────────────────────────────
        self._construir_interface()
        self._carregar_csv_inicial()
        self.janela.after(200, self._processar_fila)

    # ═══════════════════════════════════════════════════════════════════════
    #  CONSTRUÇÃO DA INTERFACE
    # ═══════════════════════════════════════════════════════════════════════

    def _construir_interface(self):
        # ─── TOPO: barra de título ──────────────────────────────────────
        cabecalho = ctk.CTkFrame(self.janela, height=50, corner_radius=0)
        cabecalho.pack(fill="x")
        cabecalho.pack_propagate(False)

        ctk.CTkLabel(
            cabecalho,
            text="Bot de Geração de Notas Fiscais Eletrônicas",
            font=("Segoe UI", 18, "bold"),
            text_color="#4DA8DA",
        ).pack(side="left", padx=20, pady=10)

        self.lbl_servidor = ctk.CTkLabel(
            cabecalho,
            text=" Servidor: Parado",
            font=("Segoe UI", 12),
            text_color="#FF6B6B",
        )
        self.lbl_servidor.pack(side="right", padx=20, pady=10)

        # ─── SELEÇÃO DE CSV ─────────────────────────────────────────────
        self.frame_csv = ctk.CTkFrame(self.janela)
        self.frame_csv.pack(fill="x", padx=15, pady=(12, 4))

        ctk.CTkLabel(
            self.frame_csv, text=" CSV:", font=("Segoe UI", 13, "bold")
        ).pack(side="left", padx=(10, 5))

        self.entry_csv = ctk.CTkEntry(
            self.frame_csv, textvariable=self.csv_path, font=("Consolas", 11)
        )
        self.entry_csv.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(
            self.frame_csv, text=" Selecionar", width=100,
            command=self._selecionar_csv,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            self.frame_csv, text=" Recarregar", width=100,
            fg_color="#2B7A4B", hover_color="#1E5A37",
            command=self._carregar_csv,
        ).pack(side="left", padx=(0, 10))

        # ─── ABAS ───────────────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(self.janela)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=6)

        self.tab_clientes = self.tabview.add(" Clientes")
        self.tab_logs     = self.tabview.add(" Logs")

        self._construir_aba_clientes()
        self._construir_aba_logs()

        # ─── BARRA DE PROGRESSO ─────────────────────────────────────────
        self.frame_progresso = ctk.CTkFrame(self.janela, height=80, corner_radius=0)
        self.frame_progresso.pack(fill="x", padx=15, pady=(0, 8))
        self.frame_progresso.pack_propagate(False)

        self.progress_bar = ctk.CTkProgressBar(
            self.frame_progresso, variable=self.progresso_var, height=20,
            corner_radius=8,
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(10, 2))
        self.progress_bar.set(0.0)

        ctk.CTkLabel(
            self.frame_progresso,
            textvariable=self.status_text,
            font=("Segoe UI", 11),
            text_color="#AAAAAA",
        ).pack(anchor="w", padx=18)

        # ─── BOTÕES DE AÇÃO ─────────────────────────────────────────────
        self.frame_botoes = ctk.CTkFrame(self.janela, fg_color="transparent")
        self.frame_botoes.pack(fill="x", padx=15, pady=(0, 14))

        self.btn_processar = ctk.CTkButton(
            self.frame_botoes,
            text="  Processar Clientes",
            height=42,
            font=("Segoe UI", 14, "bold"),
            command=self._iniciar_processamento,
        )
        self.btn_processar.pack(side="left", padx=(0, 10))

        self.btn_cancelar = ctk.CTkButton(
            self.frame_botoes,
            text="  Cancelar",
            height=42,
            fg_color="#8B0000", hover_color="#660000",
            state="disabled",
            command=self._cancelar_processamento,
        )
        self.btn_cancelar.pack(side="left")

        self.btn_servidor = ctk.CTkButton(
            self.frame_botoes,
            text=" Iniciar Servidor",
            height=42,
            fg_color="#2B5A7B", hover_color="#1E4A6B",
            command=self._iniciar_servidor,
        )
        self.btn_servidor.pack(side="right")

        self.btn_abrir_notas = ctk.CTkButton(
            self.frame_botoes,
            text=" Abrir Pasta Notas",
            height=42,
            fg_color="#555555", hover_color="#444444",
            command=lambda: os.startfile(PASTA_NOTAS) if os.path.exists(PASTA_NOTAS) else None,
        )
        self.btn_abrir_notas.pack(side="right", padx=(0, 10))

    # ─── Aba Clientes ───────────────────────────────────────────────────

    def _construir_aba_clientes(self):
        frame = self.tab_clientes

        self.info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.info_frame.pack(fill="x", pady=(5, 6))

        self.lbl_info = ctk.CTkLabel(
            self.info_frame,
            text=" Selecione um arquivo CSV para visualizar os clientes",
            font=("Segoe UI", 12),
        )
        self.lbl_info.pack(anchor="w", padx=5)

        # Container para a tabela
        container = ctk.CTkFrame(frame)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        frame_tabela = ctk.CTkFrame(container)
        frame_tabela.pack(fill="both", expand=True, padx=8, pady=8)

        # Scrollbars
        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical")
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal")

        colunas = ("nome", "cpf_cnpj", "email", "servico", "valor", "data")
        self.tree = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            selectmode="browse",
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        # Cabeçalhos
        self.tree.heading("nome",    text="Nome")
        self.tree.heading("cpf_cnpj", text="CPF/CNPJ")
        self.tree.heading("email",   text="E-mail")
        self.tree.heading("servico", text="Serviço")
        self.tree.heading("valor",   text="Valor (R$)")
        self.tree.heading("data",    text="Data")

        self.tree.column("nome",    width=160, minwidth=100)
        self.tree.column("cpf_cnpj", width=150, minwidth=100)
        self.tree.column("email",   width=190, minwidth=120)
        self.tree.column("servico", width=190, minwidth=120)
        self.tree.column("valor",   width=100, minwidth=80)
        self.tree.column("data",    width=100, minwidth=80)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_tabela.grid_rowconfigure(0, weight=1)
        frame_tabela.grid_columnconfigure(0, weight=1)

        # ─── Estilo escuro para a Treeview ──────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        bg = "#2B2B2B"
        fg = "#E0E0E0"
        sel_bg = "#1F538D"
        style.configure("Treeview", background=bg, foreground=fg,
                        fieldbackground=bg, font=("Segoe UI", 10), rowheight=28)
        style.map("Treeview", background=[("selected", sel_bg)])
        style.configure("Treeview.Heading", background="#3A3A3A",
                        foreground="#FFFFFF", font=("Segoe UI", 10, "bold"))
        style.map("Treeview.Heading", background=[("active", "#4A4A4A")])

    # ─── Aba Logs ───────────────────────────────────────────────────────

    def _construir_aba_logs(self):
        frame = self.tab_logs

        self.log_text = ctk.CTkTextbox(
            frame,
            font=("Consolas", 11),
            wrap="word",
            fg_color="#1E1E1E",
            text_color="#D4D4D4",
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_text.insert("1.0",
            "Bem-vindo ao Bot de Geração de NFS-e!\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1. O CSV padrão está em dados/clientes.csv\n"
            "2. Clique em Clientes para ver os dados\n"
            "3. Clique em Processar para iniciar\n"
            "4. Acompanhe o progresso em tempo real aqui\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        self.log_text.configure(state="disabled")

    # ═══════════════════════════════════════════════════════════════════════
    #  LÓGICA DO CSV
    # ═══════════════════════════════════════════════════════════════════════

    def _selecionar_csv(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo CSV de clientes",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if caminho:
            self.csv_path.set(caminho)
            self._carregar_csv()

    def _carregar_csv_inicial(self):
        if os.path.exists(self.csv_path.get()):
            self._carregar_csv()

    def _carregar_csv(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        caminho = self.csv_path.get()
        if not os.path.exists(caminho):
            self.lbl_info.configure(text=" Arquivo não encontrado: " + caminho)
            return

        try:
            from leitor import carregar_clientes
            validos, invalidos = carregar_clientes(caminho)
        except Exception as e:
            self.lbl_info.configure(text=f" Erro ao ler CSV: {e}")
            return

        if not validos and not invalidos:
            self.lbl_info.configure(text=" Nenhum registro encontrado no CSV")
            return

        for cli in validos:
            self.tree.insert("", "end", values=(
                cli.get("nome", ""),
                cli.get("cpf_cnpj", ""),
                cli.get("email", ""),
                cli.get("servico", ""),
                f"R$ {cli.get('valor', '')}",
                cli.get("data", ""),
            ))

        for inv in invalidos:
            d = inv.get("dados", {})
            self.tree.insert("", "end", values=(
                d.get("nome", "?"),
                d.get("cpf_cnpj", "?"),
                d.get("email", "?"),
                d.get("servico", "?"),
                d.get("valor", "?"),
                d.get("data", "?"),
            ), tags=("invalido",))

        self.tree.tag_configure("invalido", foreground="#FF6B6B")

        total = len(validos) + len(invalidos)
        msg = f" {len(validos)} válido(s)"
        if invalidos:
            msg += f"  |   {len(invalidos)} inválido(s) (em vermelho)"
        msg += f"  |   Total: {total} registro(s)"
        self.lbl_info.configure(text=msg)

        self.total_clientes = len(validos)
        self.invalidos = invalidos

    # ═══════════════════════════════════════════════════════════════════════
    #  SERVIDOR FLASK
    # ═══════════════════════════════════════════════════════════════════════

    def _iniciar_servidor(self, processar_apos=False, caminho_csv=None):
        """Inicia o servidor Flask em thread separada."""
        if self.servidor_rodando:
            return

        self._log(" Iniciando servidor Flask na porta 5000...")
        self._processar_apos_servidor = processar_apos
        self._caminho_pendente = caminho_csv

        self.thread_servidor = threading.Thread(
            target=self._rodar_servidor, daemon=True
        )
        self.thread_servidor.start()

        # Comea a verificar quando o servidor estiver no ar
        self.janela.after(1500, self._verificar_servidor)

    def _rodar_servidor(self):
        try:
            from servidor.app import app
            app.run(port=5000, debug=False, use_reloader=False)
        except Exception as e:
            self.fila_mensagens.put(("log", f" Erro no servidor: {e}"))

    def _verificar_servidor(self):
        """Verifica se o servidor está respondendo e atualiza a interface."""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(("127.0.0.1", 5000))
            s.close()
            self.servidor_rodando = True
            self.lbl_servidor.configure(text=" Servidor: Online", text_color="#6BFF6B")
            self.btn_servidor.configure(text=" Servidor Ativo", state="disabled")
            self._log(" Servidor Flask iniciado com sucesso em http://127.0.0.1:5000")

            # Se havia um processamento agendado, executa agora
            if self._processar_apos_servidor and self._caminho_pendente:
                caminho = self._caminho_pendente
                self._processar_apos_servidor = False
                self._caminho_pendente = None
                self._confirmar_processar(caminho)

        except Exception:
            self.janela.after(1000, self._verificar_servidor)

    # ═══════════════════════════════════════════════════════════════════════
    #  PROCESSAMENTO
    # ═══════════════════════════════════════════════════════════════════════

    def _iniciar_processamento(self):
        if self.processando:
            return

        caminho = self.csv_path.get()
        if not os.path.exists(caminho):
            messagebox.showerror("Erro", "Arquivo CSV no encontrado!")
            return

        # Verificar servidor
        if not self.servidor_rodando:
            resp = messagebox.askyesno(
                "Servidor no iniciado",
                "O servidor Flask não está rodando em http://127.0.0.1:5000.\n\n"
                "Deseja iniciá-lo automaticamente agora?\n\n"
                "Após iniciado, o processamento começará automaticamente."
            )
            if resp:
                self._iniciar_servidor(processar_apos=True, caminho_csv=caminho)
            return

        self._confirmar_processar(caminho)

    def _confirmar_processar(self, caminho):
        if not self.servidor_rodando:
            messagebox.showerror(
                "Erro",
                "O servidor Flask no est respondendo.\n"
                "Inicie-o manualmente ou clique em 'Iniciar Servidor'."
            )
            return

        self.cancelar = False
        self.processando = True
        self.progresso_var.set(0.0)

        self._log("\n" + "=" * 60)
        self._log("  INICIANDO PROCESSAMENTO")
        self._log("=" * 60 + "\n")

        self.status_text.set(" Iniciando...")
        self.btn_processar.configure(state="disabled")
        self.btn_cancelar.configure(state="normal")

        self.thread_bot = threading.Thread(
            target=self._executar_bot,
            args=(caminho,),
            daemon=True,
        )
        self.thread_bot.start()

    def _cancelar_processamento(self):
        self.cancelar = True
        self.status_text.set("  Cancelando...")
        self._log("\n  Cancelamento solicitado — aguardando término...\n")

    def _executar_bot(self, caminho_csv: str):
        """Executa o bot em thread separada com callbacks para GUI via fila."""
        fila = self.fila_mensagens

        try:
            from loguru import logger
            from leitor import carregar_clientes
            from bot import preencher_formulario, salvar_pdf, montar_caminho_pdf
            from organizador import organizar_pdf
            from relatorio import configurar_logs, salvar_relatorio
            from playwright.sync_api import sync_playwright

            # Acumula resultados localmente (thread-safe contra self.*)
            resultados = {"sucesso": [], "falha": []}

            # ── 1. Ler CSV ──────────────────────────────────────────────
            fila.put(("log", "  Carregando clientes do CSV..."))
            validos, invalidos = carregar_clientes(caminho_csv)

            if self.cancelar:
                fila.put(("log", "  Operação cancelada."))
                fila.put(("finalizado", None))
                return

            if not validos:
                fila.put(("log", "  Nenhum cliente valido encontrado."))
                fila.put(("status", "Nenhum cliente valido"))
                fila.put(("finalizado", None))
                return

            total = len(validos)
            fila.put(("total", total))
            fila.put(("log", f"  {total} cliente(s) válido(s) carregados."))

            if invalidos:
                fila.put(("log", f"  {len(invalidos)} registro(s) inválido(s) ignorados."))

            # ── 2. Configurar logs ──────────────────────────────────────
            caminho_log = configurar_logs()

            # Sink customizado para capturar logs do loguru na GUI
            def sink_gui(msg):
                fila.put(("log", str(msg).strip()))

            logger.add(sink_gui, format="{time:HH:mm:ss} | {level: <8} | {message}",
                       level="DEBUG", colorize=False)

            # ── 3. Iniciar Playwright ───────────────────────────────────
            fila.put(("log", "  Iniciando navegador (headless)..."))
            fila.put(("status", " Abrindo navegador..."))

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(60000)

                for i, cliente in enumerate(validos):
                    if self.cancelar:
                        break

                    nome = cliente["nome"]
                    fila.put(("log", f"\n━━━ [{i+1}/{total}] {nome} ━━━"))
                    fila.put(("status", f"  [{i+1}/{total}] Processando: {nome}"))

                    try:
                        preencher_formulario(page, cliente)

                        if self.cancelar:
                            break

                        caminho_pdf = montar_caminho_pdf(cliente)
                        salvar_pdf(page, caminho_pdf)

                        caminho_final = organizar_pdf(nome, caminho_pdf)

                        fila.put(("log", f"  {nome} → PDF salvo em: {caminho_final}"))
                        resultados["sucesso"].append({"nome": nome, "arquivo": caminho_final})

                    except Exception as e:
                        fila.put(("log", f"  {nome} → ERRO: {e}"))
                        resultados["falha"].append({"nome": nome, "erro": str(e)})

                    fila.put(("progresso", i + 1))

                browser.close()

            # ── 4. Finalizar ────────────────────────────────────────────
            if not self.cancelar:
                fila.put(("log", "\n" + "=" * 60))
                fila.put(("log", "  Gerando relatorio final..."))

                caminho_relatorio = salvar_relatorio(resultados, invalidos, caminho_log)

                fila.put(("log", f"  Relatorio: {caminho_relatorio}"))
                fila.put(("log", "=" * 60 + "\n"))

                sucesso = len(resultados["sucesso"])
                falha   = len(resultados["falha"])

                fila.put(("status", f"  Concluído! {sucesso} sucesso(s), {falha} falha(s)"))
                fila.put(("log", "  PROCESSAMENTO CONCLUÍDO COM SUCESSO!"))
                fila.put(("resumo", sucesso, falha, len(invalidos), caminho_log))
            else:
                fila.put(("log", "\n  Processamento cancelado pelo usuário."))
                fila.put(("status", " Cancelado"))

            fila.put(("finalizado", None))

        except Exception as e:
            fila.put(("log", f"\n  ERRO FATAL: {e}"))
            fila.put(("log", traceback.format_exc()))
            fila.put(("status", f" Erro: {e}"))
            fila.put(("finalizado", None))

    # ═══════════════════════════════════════════════════════════════════════
    #  FILA DE MENSAGENS (thread-safe)
    # ═══════════════════════════════════════════════════════════════════════

    def _processar_fila(self):
        """Consome a fila de mensagens da thread e atualiza a UI."""
        try:
            while True:
                msg = self.fila_mensagens.get_nowait()
                tipo = msg[0]

                if tipo == "log":
                    self._log(msg[1])

                elif tipo == "progresso":
                    _, valor = msg
                    if self.total_clientes > 0:
                        self.progresso_var.set(valor / self.total_clientes)

                elif tipo == "total":
                    _, total = msg
                    self.total_clientes = total

                elif tipo == "status":
                    _, texto = msg
                    self.status_text.set(texto)

                elif tipo == "resumo":
                    _, sucesso, falha, ignorados, log_path = msg
                    resumo = (
                        "  RESUMO DA EXECUÇÃO\n\n"
                        f"  Sucesso:     {sucesso}\n"
                        f"  Falhas:      {falha}\n"
                        f"  Ignorados:   {ignorados}\n\n"
                        f"  Log salvo em:\n    {log_path}"
                    )
                    messagebox.showinfo("Resumo da Execução", resumo)

                elif tipo == "finalizado":
                    self._finalizar()

        except queue.Empty:
            pass

        self.janela.after(100, self._processar_fila)

    def _log(self, texto: str):
        """Adiciona texto ao visor de logs."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", texto + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _finalizar(self):
        """Restaura a interface aps o processamento."""
        self.processando = False
        self.btn_processar.configure(state="normal")
        self.btn_cancelar.configure(state="disabled")
        self.progress_bar.set(0.0)

    # ═══════════════════════════════════════════════════════════════════════
    #  EXECUÇÃO
    # ═══════════════════════════════════════════════════════════════════════

    def run(self):
        self.janela.mainloop()


if __name__ == "__main__":
    app = Aplicacao()
    app.run()
