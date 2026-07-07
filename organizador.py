import os
import shutil
from loguru import logger


def criar_pasta_cliente(nome_cliente: str, pasta_raiz: str = "notas") -> str:
    """
    Cria uma subpasta com o nome do cliente dentro de notas/.
    Retorna o caminho da pasta criada.
    """
    nome_limpo = nome_cliente.strip().replace(" ", "_").replace("/", "-")
    caminho = os.path.join(pasta_raiz, nome_limpo)
    os.makedirs(caminho, exist_ok=True)  # não quebra se já existir
    return caminho


def mover_pdf(caminho_origem: str, pasta_destino: str) -> str:
    """
    Move o PDF para a pasta do cliente.
    Retorna o novo caminho completo do arquivo.
    """
    nome_arquivo = os.path.basename(caminho_origem)
    caminho_destino = os.path.join(pasta_destino, nome_arquivo)

    shutil.move(caminho_origem, caminho_destino)
    logger.info(f" Movido: {nome_arquivo} → {pasta_destino}")

    return caminho_destino


def organizar_pdf(nome_cliente: str, caminho_pdf: str, pasta_raiz: str = "notas") -> str:
    """
    Função principal — cria pasta e move o PDF.
    Retorna o caminho final do arquivo.
    """
    pasta_cliente = criar_pasta_cliente(nome_cliente, pasta_raiz)
    caminho_final = mover_pdf(caminho_pdf, pasta_cliente)
    return caminho_final


def listar_estrutura(pasta_raiz: str = "notas"):
    """Imprime a estrutura de pastas e arquivos gerados."""
    print(f"\n📂 {pasta_raiz}/")
    for item in sorted(os.listdir(pasta_raiz)):
        caminho = os.path.join(pasta_raiz, item)
        if os.path.isdir(caminho):
            arquivos = os.listdir(caminho)
            print(f"   └── 📁 {item}/")
            for arquivo in sorted(arquivos):
                print(f"          └──  {arquivo}")
        else:
            print(f"   └──  {item}")


# ─── Teste isolado ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Testa com um PDF fictício pra validar a lógica
    os.makedirs("notas", exist_ok=True)

    # Cria um arquivo vazio só pra testar o movimento
    caminho_teste = "notas/NF_Teste_Cliente_20260701.pdf"
    open(caminho_teste, "w").close()

    caminho_final = organizar_pdf("Teste Cliente", caminho_teste)
    print(f"Arquivo movido para: {caminho_final}")

    listar_estrutura()