"""
╔══════════════════════════════════════════════════════════════╗
║  🔨 Script de Build — PyInstaller                          ║
║  Gera o executável .exe do Bot de NFS-e                    ║
╚══════════════════════════════════════════════════════════════╝

Modo de usar:
  1. Instale as dependências:
     pip install -r requirements.txt
     pip install customtkinter pyinstaller
     playwright install chromium

  2. Execute este script:
     python build_exe.py

  3. O .exe será gerado na pasta dist/
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def limpar():
    """Remove builds anteriores."""
    for pasta in ["build", "dist"]:
        if os.path.exists(pasta):
            shutil.rmtree(pasta)
    for arquivo in ["app_gui.spec"]:
        if os.path.exists(arquivo):
            os.remove(arquivo)


def build():
    print("═" * 56)
    print("  🔨  COMPILANDO BOT DE NFS-e — INTERFACE GRÁFICA")
    print("═" * 56)
    print()

    # ─── Limpar builds anteriores ──────────────────────────────────────────
    print("🧹  Limpando builds anteriores...")
    limpar()

    # ─── Dados adicionais para incluir no .exe ──────────────────────────
    # Inclui a pasta dados/ (CSV), servidor/ e as pastas de saída
    add_data = [
        "dados;dados",
        "servidor;servidor",
    ]

    add_data_args = []
    for src_dst in add_data:
        add_data_args.append("--add-data")
        add_data_args.append(src_dst)

    # ─── Hidden imports (PyInstaller nem sempre detecta automaticamente) ───
    hidden_imports = [
        "--hidden-import", "pandas",
        "--hidden-import", "flask",
        "--hidden-import", "loguru",
        "--hidden-import", "playwright.sync_api",
        "--hidden-import", "leitor",
        "--hidden-import", "organizador",
        "--hidden-import", "relatorio",
        "--hidden-import", "bot",
    ]

    # ─── Collect-all (força inclusão de assets/packages completos) ────────────
    collect_all = [
        "--collect-all", "customtkinter",
    ]

    # ─── Comando PyInstaller ───────────────────────────────────────────────
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                # Um único .exe
        "--windowed",               # Sem console (modo GUI)
        "--name", "Bot_NFS-e",
        "--icon", "NONE",           # Sem ícone (troque por --icon icone.ico se tiver)
        "--clean",
        "--noconfirm",
    ] + add_data_args + hidden_imports + collect_all + ["app_gui.py"]

    print()
    print("  3. Notas Importantes:")
    print("     - As pastas 'notas/' e 'logs/' sero criadas pelo .exe")
    print("       no mesmo diretrio onde ele for executado.")
    print("     - O Chromium do Playwright precisa estar instalado")
    print("       (rode: playwright install chromium)")
    print()

    print("📦  Executando PyInstaller...")
    print(f"    Comando: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        print()
        print("✅  BUILD CONCLUÍDO COM SUCESSO!")
        print(f"    📁  Executável em: dist/Bot_NFS-e.exe")
        print()
        print("═" * 56)
        print("  📋  INSTRUÇÕES FINAIS")
        print("═" * 56)
        print()
        print("  1. O arquivo .exe está em: dist/Bot_NFS-e.exe")
        print()
        print("  2. Copie a pasta inteira 'dist' para onde desejar.")
        print("     O .exe já inclui os módulos internos.")
        print()
        print("  3. Para funcionar corretamente, o .exe precisa:")
        print("     - Deixar o antivírus liberar a execução")
        print("     - Ter o Chromium do Playwright instalado")
        print("       (execute: playwright install chromium)")
        print()
        print("  4. Opcional — troque o ícone:")
        print("     python build_exe.py --icone caminho/icone.ico")
        print()
    else:
        print()
        print("❌  ERRO DURANTE O BUILD!")
        print("    Verifique as mensagens acima.")
        sys.exit(1)


def instalar_dependencias():
    """Instala as dependências necessárias."""
    print("📦  Instalando dependências...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "-r", "requirements.txt",
        "customtkinter",
        "pyinstaller",
    ])
    print()
    print("🌐  Instalando Chromium para o Playwright...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build do Bot NFS-e")
    parser.add_argument("--install", action="store_true",
                        help="Instala dependências antes de buildar")
    parser.add_argument("--icone", type=str, default=None,
                        help="Caminho para arquivo .ico do executável")

    args = parser.parse_args()

    if args.install:
        instalar_dependencias()

    if args.icone:
        # Modifica o comando para incluir o ícone
        pass  # Será tratado dentro de build()

    build()
