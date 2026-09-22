import os
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key,
)

st.set_page_config(page_title="Automação de Dados com IA", page_icon="📊", layout="wide")

st.title("📊 Painel de Automação de Dados e Análise Inteligente")
st.write("Carregue o seu ficheiro CSV de vendas para processar os dados com Pandas e gerar um relatório executivo com a Groq.")

# Barra lateral para histórico de relatórios gerados
st.sidebar.header("📁 Histórico de Relatórios")
if os.path.exists("relatorio_executivo.md"):
    if st.sidebar.button("Ver Último Relatório Guardado"):
        with open("relatorio_executivo.md", "r", encoding="utf-8") as f:
            conteudo_historico = f.read()
        st.sidebar.markdown(conteudo_historico)
else:
    st.sidebar.info("Nenhum relatório anterior encontrado.")

# 1. Componente para carregar ficheiro na interface
ficheiro_carregado = st.file_uploader("Escolha um ficheiro CSV", type=["csv"])

if ficheiro_carregado is not None:
    try:
        # Lê o CSV enviado pelo utilizador
        df = pd.read_csv(ficheiro_carregado)
        
        # Validação robusta de colunas (Passo 4)
        colunas_obrigatorias = ["Produto", "Categoria", "Preco_Unitario", "Quantidade_Vendida"]
        colunas_em_falta = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_em_falta:
            st.error(f"[-] O ficheiro enviado não tem as colunas obrigatórias: {colunas_em_falta}")
        else:
            st.subheader("📋 Dados Originais Validados")
            st.dataframe(df)
            
            if st.button("Executar Análise com IA"):
                with st.spinner("A processar dados e a contactar a IA da Groq..."):
                    # Processamento com Pandas
                    df["Faturamento_Total"] = df["Preco_Unitario"] * df["Quantidade_Vendida"]
                    dados_em_texto = df.to_csv(index=False)
                    
                    # Chamada à API da Groq
                    response = client.chat.completions.create(
                        model="openai/gpt-oss-safeguard-20b",
                        messages=[
                            {"role": "system", "content": "Você é um analista de dados sénior especialista em relatórios executivos."},
                            {"role": "user", "content": f"Elabore um sumário executivo detalhado com base nestes dados:\n\n{dados_em_texto}"}
                        ],
                    )
                    
                    relatorio_ia = response.choices[0].message.content
                    
                    st.success("Análise concluída com sucesso!")
                    
                    st.subheader("📑 Relatório Executivo Gerado pela IA")
                    st.markdown(relatorio_ia)
                    
                    # Guarda automaticamente no disco para o histórico
                    with open("relatorio_executivo.md", "w", encoding="utf-8") as f:
                        f.write("# Relatório Executivo Automatizado\n\n")
                        f.write(relatorio_ia)
                    
                    # Opção para descarregar o relatório em Markdown
                    st.download_button(
                        label="Descarregar Relatório (.md)",
                        data=relatorio_ia,
                        file_name="relatorio_executivo.md",
                        mime="text/markdown"
                    )
                    
    except Exception as e:
        st.error(f"Erro ao processar o ficheiro: {e}")