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
st.write("Carregue o seu ficheiro CSV para processar os dados, pré-visualizar análises e gráficos, e validar tudo antes de descarregar.")

# Barra lateral para histórico de relatórios guardados
st.sidebar.header("📁 Histórico de Relatórios")
if os.path.exists("relatorio_executivo.md"):
    if st.sidebar.button("Ver Último Relatório Guardado"):
        with open("relatorio_executivo.md", "r", encoding="utf-8") as f:
            conteudo_historico = f.read()
        st.sidebar.markdown(conteudo_historico)
else:
    st.sidebar.info("Nenhum relatório anterior encontrado.")

# Componente para carregar ficheiro na interface
ficheiro_carregado = st.file_uploader("Escolha um ficheiro CSV", type=["csv"])

if ficheiro_carregado is not None:
    try:
        # Lê o CSV enviado pelo utilizador
        df = pd.read_csv(ficheiro_carregado)
        
        # Validação robusta de colunas obrigatórias
        colunas_obrigatorias = ["Produto", "Categoria", "Preco_Unitario", "Quantidade_Vendida"]
        colunas_em_falta = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_em_falta:
            st.error(f"[-] O ficheiro enviado não tem as colunas obrigatórias: {colunas_em_falta}")
        else:
            st.subheader("📋 Dados Originais Validados")
            st.dataframe(df)
            
            if st.button("Executar Análise com IA e Gerar Pré-visualização"):
                with st.spinner("A processar dados, a desenhar gráficos e a contactar a IA da Groq..."):
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
                    
                    # Guarda na sessão do Streamlit para manter a pré-visualização ativa
                    st.session_state["relatorio_atual"] = relatorio_ia
                    st.session_state["df_processado"] = df
                    
                    # Guarda também no disco para o histórico lateral
                    with open("relatorio_executivo.md", "w", encoding="utf-8") as f:
                        f.write("# Relatório Executivo Automatizado\n\n")
                        f.write(relatorio_ia)
                
                st.success("Análise e pré-visualização geradas com sucesso!")

            # Se já existir um relatório gerado na sessão, mostra a pré-visualização e os gráficos antes do download
            if "relatorio_atual" in st.session_state:
                st.divider()
                st.header("🔍 Pré-visualização Antes do Download")
                
                # Divisão em abas para organizar a pré-visualização (Texto vs Gráficos)
                aba_texto, aba_graficos = st.tabs(["📄 Pré-visualização do Relatório", "📈 Pré-visualização de Gráficos"])
                
                with aba_texto:
                    st.info("Verifique abaixo o conteúdo exato que será gravado no ficheiro final:")
                    st.markdown(st.session_state["relatorio_atual"])
                
                with aba_graficos:
                    st.info("Validação visual do faturamento total por produto:")
                    df_graf = st.session_state["df_processado"]
                    if "Produto" in df_graf.columns and "Faturamento_Total" in df_graf.columns:
                        # Cria um gráfico de barras interativo nativo do Streamlit
                        st.bar_chart(df_graf.set_index("Produto")["Faturamento_Total"])
                
                st.divider()
                # Botão final de download só aparece após a validação na pré-visualização
                st.download_button(
                    label="📥 Confirmar e Descarregar Relatório (.md)",
                    data=st.session_state["relatorio_atual"],
                    file_name="relatorio_executivo.md",
                    mime="text/markdown"
                )
                    
    except Exception as e:
        st.error(f"Erro ao processar o ficheiro: {e}")