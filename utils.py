import pandas as pd
from config import COLUNAS_OBRIGATORIAS

def validar_e_processar_dados(df):
    """
    Valida as colunas obrigatórias, deteta anomalias (valores negativos ou nulos)
    e calcula o faturamento total.
    """
    colunas_em_falta = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
    
    if colunas_em_falta:
        return None, f"O ficheiro não contém as colunas obrigatórias: {colunas_em_falta}"
    
    df_proc = df.copy()
    
    # Auditoria de anomalias: valores negativos ou valores nulos/em branco
    tem_negativos = (df_proc["Preco_Unitario"] < 0).any() or (df_proc["Quantidade_Vendida"] < 0).any()
    tem_nulos = df_proc[COLUNAS_OBRIGATORIAS].isnull().any().any()
    
    # Cálculo base do faturamento total
    df_proc["Faturamento_Total"] = df_proc["Preco_Unitario"] * df_proc["Quantidade_Vendida"]
    
    anomalias = {
        "negativos": tem_negativos,
        "nulos": tem_nulos
    }
    
    return df_proc, anomalias