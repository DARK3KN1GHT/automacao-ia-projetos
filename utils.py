import pandas as pd
from config import COLUNAS_OBRIGATORIAS

def validar_e_processar_dados(df):
    """
    Valida as colunas obrigatórias com base no config.py, deteta anomalias 
    (valores negativos) e calcula métricas derivadas de faturamento.
    """
    colunas_em_falta = [col for col in COLUNAS_OBRIGATORIAS if col not in df.columns]
    
    if colunas_em_falta:
        return None, f"O ficheiro não contém as colunas obrigatórias: {colunas_em_falta}"
    
    df_proc = df.copy()
    
    # Auditoria de anomalias (preços ou quantidades negativas)
    tem_negativos = (df_proc["Preco_Unitario"] < 0).any() or (df_proc["Quantidade_Vendida"] < 0).any()
    
    # Cálculo base do faturamento total por linha
    df_proc["Faturamento_Total"] = df_proc["Preco_Unitario"] * df_proc["Quantidade_Vendida"]
    
    return df_proc, tem_negativos