import pandas as pd

def validar_e_processar_dados(df):
    auditoria = {"negativos": False, "nulos": False}
    colunas_necessarias = ["Produto", "Categoria", "Preco_Unitario", "Quantidade_Vendida"]
    for col in colunas_necessarias:
        if col not in df.columns:
            return None, f"Coluna obrigatória em falta: {col}"
            
    if df[colunas_necessarias].isnull().sum().sum() > 0:
        auditoria["nulos"] = True
        df = df.dropna(subset=colunas_necessarias)
        
    if (df["Preco_Unitario"] < 0).any() or (df["Quantidade_Vendida"] < 0).any():
        auditoria["negativos"] = True
        df = df[(df["Preco_Unitario"] >= 0) & (df["Quantidade_Vendida"] >= 0)]
        
    df["Faturamento_Total"] = df["Preco_Unitario"] * df["Quantidade_Vendida"]
    return df, auditoria

def formatar_moeda_br(valor):
    """
    Formata estritamente para o padrão monetário brasileiro: R$ X.XXX,XX
    Exemplo: 163550.0 -> R$ 163.550,00
    """
    # Formata com separadores padrão e depois inverte para o padrão PT-BR
    s = f"{valor:,.2f}"
    s = s.replace(",", "V").replace(".", ",").replace("V", ".")
    return f"R$ {s}"

def formatar_percentual_br(valor):
    return f"{valor:.2f}%".replace(".", ",")