import os
import io
import re
import zipfile
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Importação dos módulos da nossa arquitetura modular sénior
from config import PROMPTS_SISTEMA, COLUNAS_OBRIGATORIAS
from utils import validar_e_processar_dados
from excel_generator import gerar_excel_executivo
from charts import renderizar_graficos_analiticos
from pdf_generator import gerar_pdf_executivo

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
st.markdown("Plataforma avançada para validação de dados, monitoramento de KPIs corporativos, relatórios gerados por IA e exportação executiva.")

st.divider()

# --- BARRA LATERAL (CONFIGURAÇÕES E HISTÓRICO) ---
st.sidebar.markdown("### 🎛️ Painel de Controle")

st.sidebar.markdown("#### 🔑 Credenciais")
api_key_input = st.sidebar.text_input("Chave API da Groq:", type="password", value=os.environ.get("GROQ_API_KEY", ""))

st.sidebar.divider()
st.sidebar.markdown("#### ⚙️ Motor de IA")
tom_relatorio = st.sidebar.selectbox(
    "Tom do Relatório:",
    list(PROMPTS_SISTEMA.keys())
)

if "tom_anterior" not in st.session_state:
    st.session_state["tom_anterior"] = tom_relatorio

if st.session_state["tom_anterior"] != tom_relatorio:
    st.session_state["tom_anterior"] = tom_relatorio

st.sidebar.divider()
st.sidebar.markdown("#### 📂 Histórico de Relatórios")
if os.path.exists("relatorio_executivo.md"):
    if st.sidebar.button("📄 Carregar Último Relatório Salvo", width='stretch'):
        with open("relatorio_executivo.md", "r", encoding="utf-8") as f:
            st.session_state["relatorio_atual"] = f.read()
        st.sidebar.success("Relatório carregado com sucesso!")
else:
    st.sidebar.info("Nenhum relatório anterior guardado.")

# --- CORPO PRINCIPAL: IMPORTAÇÃO DE DADOS (MULTI-UPLOAD) ---
st.markdown("### 📥 Importação de Arquivos de Dados")
ficheiros_carregados = st.file_uploader(
    f"Arraste ou selecione um ou mais arquivos CSV (colunas obrigatórias: {', '.join(COLUNAS_OBRIGATORIAS)})", 
    type=["csv"], 
    accept_multiple_files=True
)

if ficheiros_carregados:
    try:
        # Consolidação de múltiplos ficheiros
        lista_dfs = [pd.read_csv(f) for f in ficheiros_carregados]
        df_bruto = pd.concat(lista_dfs, ignore_index=True)
        
        # Validação e Processamento via módulo utilitário
        df, auditoria = validar_e_processar_dados(df_bruto)
        
        if df is None:
            st.error(f"❌ Erro de Validação: {auditoria}")
        else:
            if auditoria["negativos"]:
                st.warning("⚠️ **Aviso de Auditoria:** Foram detetados valores negativos nos preços ou quantidades.")
            if auditoria["nulos"]:
                st.warning("⚠️ **Aviso de Auditoria:** Foram detetados campos em branco ou valores nulos (NaN) nos dados.")

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
            
            st.markdown(f"### 📊 Indicadores-Chave de Desempenho (KPIs) — *{categoria_selecionada}*")
            
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric(label="💰 Faturamento Total", value=f"R$ {total_faturamento:,.2f}", delta="Consolidado")
            with kpi2:
                st.metric(label="📦 Volume Total Vendido", value=f"{total_quantidade:,} un", delta="Estoque/Saída")
            with kpi3:
                st.metric(label="🏷️ Ticket Médio Global", value=f"R$ {ticket_medio:,.2f}", delta="Média por Item")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- TABELA DE DADOS VALIDADOS ---
            with st.expander("🔍 Ver Tabela de Dados Detalhada (Expandir/Recolher)", expanded=False):
                st.dataframe(df_filtrado, width='stretch')
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- BOTÃO DE EXECUÇÃO DA IA ---
            col_acao1, col_acao2, col_acao3 = st.columns([1, 2, 1])
            with col_acao2:
                botao_executar = st.button("🚀 Executar Análise Inteligente com IA", width='stretch', type="primary")
            
            if botao_executar:
                if not api_key_input:
                    st.error("⚠️ Insira a sua Chave API da Groq na barra lateral para prosseguir.")
                else:
                    client = OpenAI(
                        base_url="https://api.groq.com/openai/v1",
                        api_key=api_key_input,
                    )
                    
                    with st.spinner(f"✨ A processar análise estratégica com o tom '{tom_relatorio}'..."):
                        resumo_categorias = df_filtrado.groupby("Categoria").agg(
                            Faturamento=("Faturamento_Total", "sum"),
                            Quantidade=("Quantidade_Vendida", "sum")
                        ).reset_index()
                        
                        resumo_categorias["Percentual_Faturamento"] = (resumo_categorias["Faturamento"] / total_faturamento) * 100
                        
                        tabela_resumo_texto = resumo_categorias.to_string(index=False)
                        dados_em_texto = df_filtrado.to_csv(index=False)
                        
                        contexto_metricas = (
                            f"\n\n[DADOS OFICIAIS CALCULADOS - PROIBIDO ALTERAR ESTES NÚMEROS]:\n"
                            f"- Faturamento Total: R$ {total_faturamento:,.2f}\n"
                            f"- Quantidade Total Vendida: {total_quantidade:,} unidades\n"
                            f"- Ticket Médio Global: R$ {ticket_medio:,.2f}\n\n"
                            f"Resumo Oficial por Categoria (Utilize obrigatoriamente estes valores na tabela):\n"
                            f"{tabela_resumo_texto}\n"
                        )
                        
                        system_prompt = PROMPTS_SISTEMA[tom_relatorio]
                        
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-safeguard-20b",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Elabore um relatório executivo de alta performance utilizando estritamente os dados oficiais calculados abaixo, garantindo obrigatoriamente o símbolo monetário 'R$' colado aos valores e sem citar estoques inexistentes:\n\n{contexto_metricas}\n\nDados detalhados:\n{dados_em_texto}"}
                            ],
                        )
                        
                        relatorio_ia = response.choices[0].message.content
                        
                        # =========================================================================
                        # PÓS-PROCESSADOR INTELIGENTE POR REGEX (BLINDAGEM ABSOLUTA DE DADOS E FORMATO)
                        # =========================================================================
                        
                        # 1. Captura QUALQUER variação de 'R' solto antes de números e força 'R$'
                        relatorio_ia = re.sub(r'\bR\s+(?=\d)', 'R$ ', relatorio_ia)
                        relatorio_ia = re.sub(r'\bR(?=\s*[\d\.,]+)', 'R$ ', relatorio_ia)
                        
                        # 2. Limpeza de erros conceituais de estoque
                        relatorio_ia = (
                            relatorio_ia.replace("em estoque", "comercializadas")
                                        .replace("unidades em estoque", "unidades comercializadas")
                                        .replace("estoque logístico", "escoamento logístico")
                                        .replace("estoque", "vendas")
                        )
                        
                        # 3. Substituições cirúrgicas de termos e vocabulário
                        relatorio_ia = (
                            relatorio_ia.replace("Rato", "Mouse")
                                        .replace("rato", "mouse")
                                        .replace("quase metade", "mais de um terço")
                                        .replace("gama média", "categoria média")
                                        .replace("alta gama", "alta performance")
                                        .replace("Mouse Gamer Wireless (mouse)", "Mouse Gamer Wireless")
                                        .replace("keyboards", "teclados")
                                        .replace("Keyboard", "Teclado")
                        )
                        
                        # Garante duplicação zero de cifrões
                        relatorio_ia = relatorio_ia.replace("R$$", "R$")
                        
                        st.session_state["relatorio_atual"] = relatorio_ia
                        st.session_state["df_processado"] = df_filtrado
                        
                        with open("relatorio_executivo.md", "w", encoding="utf-8") as f:
                            f.write(f"# Relatório Executivo ({tom_relatorio} - {categoria_selecionada})\n\n")
                            f.write(relatorio_ia)
                    
                    st.success("🎉 Análise avançada gerada com sucesso e pronta para revisão!")

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
                    renderizar_graficos_analiticos(df_graf)
                
                st.divider()
                st.markdown("## 📥 Exportação de Resultados Profissionais")
                
                # --- GERAÇÃO DE FICHEIROS ATRAVÉS DOS MÓDULOS ---
                df_excel = st.session_state["df_processado"]
                excel_bytes = gerar_excel_executivo(df_excel, total_faturamento, total_quantidade, ticket_medio)
                pdf_bytes = gerar_pdf_executivo(st.session_state["relatorio_atual"], categoria_selecionada, tom_relatorio)

                # Criar Pacote ZIP em memória contendo Markdown, Excel e PDF
                zip_output = io.BytesIO()
                with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.writestr("relatorio_executivo.md", st.session_state["relatorio_atual"])
                    zipf.writestr("relatorio_vendas_executivo.xlsx", excel_bytes)
                    zipf.writestr("relatorio_executivo.pdf", pdf_bytes)
                zip_bytes = zip_output.getvalue()

                # Botões de Download em 4 colunas harmoniosas
                col_down1, col_down2, col_down3, col_down4 = st.columns(4)
                
                with col_down1:
                    st.download_button(
                        label="📄 Relatório Markdown (.md)",
                        data=st.session_state["relatorio_atual"],
                        file_name="relatorio_executivo.md",
                        mime="text/markdown",
                        width='stretch'
                    )
                
                with col_down2:
                    st.download_button(
                        label="📊 Excel Executivo (.xlsx)",
                        data=excel_bytes,
                        file_name="relatorio_vendas_executivo.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width='stretch'
                    )

                with col_down3:
                    st.download_button(
                        label="📑 Relatório PDF (.pdf)",
                        data=pdf_bytes,
                        file_name="relatorio_executivo.pdf",
                        mime="application/pdf",
                        width='stretch'
                    )

                with col_down4:
                    st.download_button(
                        label="📦 Pacote Completo (.zip)",
                        data=zip_bytes,
                        file_name="pacote_relatorio_executivo.zip",
                        mime="application/zip",
                        width='stretch'
                    )
                    
    except Exception as e:
        st.error(f"❌ Ocorreu um erro ao processar o ficheiro: {e}")