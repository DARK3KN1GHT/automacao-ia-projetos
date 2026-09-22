import os
import io
import zipfile
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Importação dos módulos arquiteturais e configurações
from config import PROMPTS_SISTEMA, COLUNAS_OBRIGATORIAS
from utils import validar_e_processar_dados
from excel_generator import gerar_excel_executivo

# Carrega as variáveis de ambiente iniciais
load_dotenv()

# Configuração da Página com layout largo (Wide)
st.set_page_config(
    page_title="Analytics & AI Enterprise Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS CORPORATIVA PROFISSIONAL ---
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    hr {
        margin: 1.5rem 0;
        border-color: #2A3441;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO DA APLICAÇÃO ---
st.title("⚡ Enterprise Data & AI Intelligence Hub")
st.markdown("Plataforma avançada para validação de dados, monitorização de KPIs corporativos, relatórios gerados por IA e exportação executiva.")

st.divider()

# --- BARRA LATERAL (CONFIGURAÇÕES E HISTÓRICO) ---
st.sidebar.markdown("### 🎛️ Painel de Controlo")

st.sidebar.markdown("#### 🔑 Credenciais")
api_key_input = st.sidebar.text_input("Chave API da Groq:", type="password", value=os.environ.get("GROQ_API_KEY", ""))

st.sidebar.divider()
st.sidebar.markdown("#### ⚙️ Motor de IA")
tom_relatorio = st.sidebar.selectbox(
    "Tom do Relatório:",
    list(PROMPTS_SISTEMA.keys())
)

# Gestão inteligente de estado para mudança de tom sem apagar relatórios ativos
if "tom_anterior" not in st.session_state:
    st.session_state["tom_anterior"] = tom_relatorio

if st.session_state["tom_anterior"] != tom_relatorio:
    st.session_state["tom_anterior"] = tom_relatorio
    # Mantém o relatório atual em sessão, mas regista a mudança de tom

st.sidebar.divider()
st.sidebar.markdown("#### 📂 Histórico de Relatórios")
if os.path.exists("relatorio_executivo.md"):
    if st.sidebar.button("📄 Carregar Último Relatório Salvo", use_container_width=True):
        with open("relatorio_executivo.md", "r", encoding="utf-8") as f:
            st.session_state["relatorio_atual"] = f.read()
        st.sidebar.success("Relatório carregado com sucesso!")
else:
    st.sidebar.info("Nenhum relatório anterior guardado.")

# --- CORPO PRINCIPAL: IMPORTAÇÃO DE DADOS (MULTI-UPLOAD) ---
st.markdown("### 📥 Importação de Ficheiros de Dados")
ficheiros_carregados = st.file_uploader(
    f"Arraste ou selecione um ou mais ficheiros CSV (colunas obrigatórias: {', '.join(COLUNAS_OBRIGATORIAS)})", 
    type=["csv"], 
    accept_multiple_files=True
)

if ficheiros_carregados:
    try:
        # Consolidação de múltiplos ficheiros
        lista_dfs = [pd.read_csv(f) for f in ficheiros_carregados]
        df_bruto = pd.concat(lista_dfs, ignore_index=True)
        
        # Validação e Processamento via módulo utilitário
        df, tem_negativos = validar_e_processar_dados(df_bruto)
        
        if df is None:
            st.error(f"❌ Erro de Validação: {tem_negativos}")
        else:
            if tem_negativos:
                st.warning("⚠️ **Aviso de Auditoria:** Foram detetados valores negativos nos preços ou quantidades. Os cálculos analíticos podem ser comprometidos.")

            # --- FILTRAGEM DINÂMICA NA BARRA LATERAL ---
            st.sidebar.divider()
            st.sidebar.markdown("#### 🔍 Filtros Analíticos")
            categorias_disponiveis = ["Todas"] + list(df["Categoria"].unique())
            categoria_selecionada = st.sidebar.selectbox("Filtrar por Categoria:", categorias_disponiveis)
            
            if categoria_selecionada != "Todas":
                df_filtrado = df[df["Categoria"] == categoria_selecionada].copy()
            else:
                df_filtrado = df.copy()
            
            st.divider()
            
            # --- CARTÕES DE MÉTRICAS (KPIs EXECUTIVOS) ---
            total_faturamento = df_filtrado["Faturamento_Total"].sum()
            total_quantidade = df_filtrado["Quantidade_Vendida"].sum()
            ticket_medio = total_faturamento / total_quantidade if total_quantidade > 0 else 0
            
            st.markdown(f"### 📊 Indicadores Chave de Desempenho (KPIs) — *{categoria_selecionada}*")
            
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric(label="💰 Faturamento Total", value=f"R$ {total_faturamento:,.2f}", delta="Consolidado")
            with kpi2:
                st.metric(label="📦 Volume Total Vendido", value=f"{total_quantidade:,} un", delta="Stock/Saída")
            with kpi3:
                st.metric(label="🏷️ Ticket Médio Global", value=f"R$ {ticket_medio:,.2f}", delta="Média por Item")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- TABELA DE DADOS VALIDADOS ---
            with st.expander("🔍 Ver Tabela de Dados Detalhada (Expandir/Recolher)", expanded=False):
                st.dataframe(df_filtrado, use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- BOTÃO DE EXECUÇÃO DA IA ---
            col_acao1, col_acao2, col_acao3 = st.columns([1, 2, 1])
            with col_acao2:
                botao_executar = st.button("🚀 Executar Análise Inteligente com IA", use_container_width=True, type="primary")
            
            if botao_executar:
                if not api_key_input:
                    st.error("⚠️ Insira a sua Chave API da Groq na barra lateral para prosseguir.")
                else:
                    client = OpenAI(
                        base_url="https://api.groq.com/openai/v1",
                        api_key=api_key_input,
                    )
                    
                    with st.spinner(f"✨ A processar análise estratégica com o tom '{tom_relatorio}'..."):
                        dados_em_texto = df_filtrado.to_csv(index=False)
                        system_prompt = PROMPTS_SISTEMA[tom_relatorio]
                        
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-safeguard-20b",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Elabore um relatório executivo de alta performance com base nestes dados:\n\n{dados_em_texto}"}
                            ],
                        )
                        
                        relatorio_ia = response.choices[0].message.content
                        
                        st.session_state["relatorio_atual"] = relatorio_ia
                        st.session_state["df_processado"] = df_filtrado
                        
                        with open("relatorio_executivo.md", "w", encoding="utf-8") as f:
                            f.write(f"# Relatório Executivo ({tom_relatorio} - {categoria_selecionada})\n\n")
                            f.write(relatorio_ia)
                    
                    st.success("🎉 Análise avançada gerada com sucesso!")
                    st.balloons()

            # --- PRÉ-VISUALIZAÇÃO ANTES DO DOWNLOAD ---
            if "relatorio_atual" in st.session_state:
                st.divider()
                st.markdown("## 🔍 Pré-visualização e Validação Visual")
                
                aba_texto, aba_graficos = st.tabs(["📄 Relatório Estratégico (Markdown)", "📈 Gráficos Analíticos Avançados"])
                
                with aba_texto:
                    st.info(f"Modo Ativo: **{tom_relatorio}** | Filtro Aplicado: **{categoria_selecionada}**")
                    st.markdown(st.session_state["relatorio_atual"])
                
                with aba_graficos:
                    st.markdown("#### Análise Gráfica Comparativa de Desempenho")
                    df_graf = st.session_state["df_processado"]
                    if "Produto" in df_graf.columns:
                        # Gráficos individuais por produto
                        col_g1, col_g2 = st.columns(2)
                        with col_g1:
                            st.markdown("**Faturamento por Produto (R$)**")
                            st.bar_chart(df_graf.set_index("Produto")["Faturamento_Total"], color="#3B82F6")
                        with col_g2:
                            st.markdown("**Volume Vendido por Produto (Unidades)**")
                            st.bar_chart(df_graf.set_index("Produto")["Quantidade_Vendida"], color="#10B981")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # NOVO GRÁFICO 3: Faturamento Agregado por Categoria
                        st.markdown("#### 📊 Distribuição Consolidada de Faturamento por Categoria")
                        df_categoria = df_graf.groupby("Categoria")["Faturamento_Total"].sum()
                        st.bar_chart(df_categoria, color="#8B5CF6")
                
                st.divider()
                st.markdown("## 📥 Exportação de Resultados Profissionais")
                
                # --- GERAÇÃO DE FICHEIROS ATRAVÉS DOS MÓDULOS ---
                df_excel = st.session_state["df_processado"]
                excel_bytes = gerar_excel_executivo(df_excel, total_faturamento, total_quantidade, ticket_medio)

                # Criar Pacote ZIP em memória
                zip_output = io.BytesIO()
                with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.writestr("relatorio_executivo.md", st.session_state["relatorio_atual"])
                    zipf.writestr("relatorio_vendas_executivo.xlsx", excel_bytes)
                zip_bytes = zip_output.getvalue()

                # Botões de Download em colunas harmoniosas
                col_down1, col_down2, col_down3 = st.columns(3)
                
                with col_down1:
                    st.download_button(
                        label="📄 Relatório Markdown (.md)",
                        data=st.session_state["relatorio_atual"],
                        file_name="relatorio_executivo.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                with col_down2:
                    st.download_button(
                        label="📊 Excel Executivo (.xlsx)",
                        data=excel_bytes,
                        file_name="relatorio_vendas_executivo.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                with col_down3:
                    st.download_button(
                        label="📦 Descarregar Pacote Completo (.zip)",
                        data=zip_bytes,
                        file_name="pacote_relatorio_executivo.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    
    except Exception as e:
        st.error(f"❌ Ocorreu um erro ao processar o ficheiro: {e}")