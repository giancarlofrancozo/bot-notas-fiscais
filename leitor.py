import pandas as pd
from loguru import logger

COLUNAS_OBRIGATORIAS = ["nome", "cpf_cnpj", "email", "servico", "valor", "data"]

def carregar_clientes (caminho_csv: str) -> tuple[list[dict], list[dict]]:

    """""
    Lê o CSV, valida cada linha e separa válidos de inválidos.
    Retorna: (clientes_validos, clientes_invalidos)

    """""

    logger.info(f'lendo o arquivo: {caminho_csv}')
    try:
        df = pd.read_csv(caminho_csv)
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {caminho_csv}")
        return [], []

    #verificar se a coluna existe
    colunas_faltando = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
    if colunas_faltando:
        logger.error(f"Colunas obrigatórias faltando: {colunas_faltando}")
        return [], []
    
    validos = []
    invalidos = []

    for i, row in df.iterrows():
        erros = validar_linha(row, i + 2)  # +2 para considerar o cabeçalho e índice 0
        if erros:
            invalidos.append({
            "linha": i + 2,
            "dados": row.to_dict(),
            "erros": erros}) 
            logger.warning(f"Linha {i + 2} inválida: {erros}")
        else:
            validos.append(row.to_dict())
            logger.info(f"Linha {i + 2} válida: {row.to_dict()}")
        
    logger.info(f"Resultado: {len(validos)} válidos, {len(invalidos)} inválidos")
    return validos, invalidos

def validar_linha(row: pd.Series, num_linha: int) -> list[str]:
    """Retorna lista de erros da linha. Lista vazia = linha válida."""
    erros = []

    for campo in COLUNAS_OBRIGATORIAS:
        valor = row.get(campo)
        if pd.isna(valor) or str(valor).strip() == "":
            erros.append(f"Campo '{campo}' está vazio")

    try:
        valor_float = float(row.get("valor", 0))
        if valor_float <= 0:
            erros.append("Campo 'valor' deve ser maior que zero")
    except (ValueError, TypeError):
        erros.append("Campo 'valor' não é um número válido")

    return erros


if __name__ == "__main__":
    validos, invalidos = carregar_clientes("dados/clientes.csv")

    print("\n CLIENTES VÁLIDOS:")
    for c in validos:
        print(f"  → {c['nome']} | {c['servico']} | R$ {c['valor']}")

    print("\n CLIENTES INVÁLIDOS:")
    for c in invalidos:
        print(f"  → Linha {c['linha']}: {c['erros']}")

            
