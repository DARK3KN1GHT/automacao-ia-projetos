import os
import io
import re
import zipfile
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

from config import PROMPTS_SISTEMA, COLUNAS_OBRIGATORIAS
from utils import validar_e_processar_dados, formatar_moeda_br, formatar_percentual_br
from excel_generator import gerar_excel_executivo
from charts import renderizar_graficos_analiticos
from pdf_generator import gerar_pdf_executivo

load_dotenv()

st.set_page_config(page_title="Analytics & AI Enterprise Hub", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 700; letter-spacing: -0.5px; }
    hr { margin: 1.5rem 0; border-color: #2A3441; }
    [data-testid="stFileUploadDropzone"] div { padding-top: 10px; padding-bottom: 10px; }
    .stMarkdown table { width: 100%; }
    .stMarkdown table th, .stMarkdown table td { white-space: nowrap !important; }
    .stMarkdown table th:nth-child(1), .stMarkdown table td:nth-child(1) { text-align: left !important; }
    .stMarkdown table th:nth-child(n+2), .stMarkdown table td:nth-child(n+2) { text-align: right !important; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Enterprise Data & AI Intelligence Hub")
st.markdown("Plataforma avançada para validação de dados, monitoramento de KPIs corporativos, relatórios gerados por IA e exportação executiva.")
st.divider()

st.sidebar.markdown("### 🎛️ Painel de Controle")
api_key_input = st.sidebar.text_input("Chave API da Groq:", type="password", value=os.environ.get("GROQ_API_KEY", ""))
st.sidebar.divider()
tom_relatorio = st.sidebar.selectbox("Tom do Relatório:", list(PROMPTS_SISTEMA.keys()))

if "tom_anterior" not in st.session_state: st.session_state["tom_anterior"] = tom_relatorio
if st.session_state["tom_anterior"] != tom_relatorio: st.session_state["tom_anterior"] = tom_relatorio

st.sidebar.divider()
st.sidebar.markdown("#### 📂 Histórico de Relatórios")
if os.path.exists("relatorio_executivo.md"):
    if st.sidebar.button("📄 Carregar Último Relatório Salvo", use_container_width=True):
        with open("relatorio_executivo.md", "r", encoding="utf-8") as f:
            st.session_state["relatorio_atual"] = f.read()
        st.sidebar.success("Relatório carregado com sucesso!")
else:
    st.sidebar.info("Nenhum relatório anterior guardado.")

st.markdown("### 📥 Importação de Arquivos de Dados")
ficheiros_carregados = st.file_uploader(
    f"Arraste ou selecione um ou mais arquivos CSV (colunas obrigatórias: {', '.join(COLUNAS_OBRIGATORIAS)})", 
    type=["csv"], accept_multiple_files=True, label_visibility="visible"
)

if ficheiros_carregados:
    try:
        ficheiros_unicos = {f.name: f for f in ficheiros_carregados}.values()
        lista_dfs = [pd.read_csv(f) for f in ficheiros_unicos]
        df_bruto = pd.concat(lista_dfs, ignore_index=True)
        
        df, auditoria = validar_e_processar_dados(df_bruto)
        
        if df is None:
            st.error(f"❌ Erro de Validação: {auditoria}")
        else:
            if auditoria["negativos"]: st.warning("⚠️ Foram detetados valores negativos nos preços ou quantidades.")
            if auditoria["nulos"]: st.warning("⚠️ Foram detetados campos em branco ou nulos (NaN) nos dados.")

            st.sidebar.divider()
            st.sidebar.markdown("#### 🔍 Filtros Analíticos")
            categorias_disponiveis = ["Todas"] + list(df["Categoria"].unique())
            categoria_selecionada = st.sidebar.selectbox("Filtrar por Categoria:", categorias_disponiveis)
            
            df_filtrado = df[df["Categoria"] == categoria_selecionada].copy() if categoria_selecionada != "Todas" else df.copy()
            st.divider()
            
            total_faturamento = df_filtrado["Faturamento_Total"].sum()
            total_quantidade = df_filtrado["Quantidade_Vendida"].sum()
            ticket_medio = total_faturamento / total_quantidade if total_quantidade > 0 else 0
            
            st.markdown(f"### 📊 Indicadores-Chave de Desempenho (KPIs) — *{categoria_selecionada}*")
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1: st.metric(label="💰 Faturamento Total", value=formatar_moeda_br(total_faturamento), delta="Consolidado")
            with kpi2: st.metric(label="📦 Volume Total Vendido", value=f"{total_quantidade:,} unid.".replace(",", "."), delta="Saída Comercial")
            with kpi3: st.metric(label="🏷️ Ticket Médio Global", value=formatar_moeda_br(ticket_medio), delta="Média por Item")
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.expander("🔍 Ver Tabela de Dados Detalhada (Expandir/Recolher)", expanded=False):
                st.dataframe(df_filtrado, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_acao1, col_acao2, col_acao3 = st.columns([1, 2, 1])
            with col_acao2: botao_executar = st.button("🚀 Executar Análise Inteligente com IA", use_container_width=True, type="primary")
            
            if botao_executar:
                if not api_key_input:
                    st.error("⚠️ Insira a sua Chave API da Groq na barra lateral para prosseguir.")
                else:
                    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key_input)
                    with st.spinner(f"✨ A processar análise estratégica com o tom '{tom_relatorio}'..."):
                        
                        resumo_categorias = df_filtrado.groupby("Categoria").agg(
                            Faturamento=("Faturamento_Total", "sum"), Quantidade=("Quantidade_Vendida", "sum")
                        ).reset_index()
                        resumo_categorias["Percentual_Faturamento"] = (resumo_categorias["Faturamento"] / total_faturamento) * 100
                        
                        resumo_categorias_fmt = resumo_categorias.copy()
                        resumo_categorias_fmt["Faturamento"] = resumo_categorias_fmt["Faturamento"].apply(formatar_moeda_br)
                        resumo_categorias_fmt["Percentual_Faturamento"] = resumo_categorias_fmt["Percentual_Faturamento"].apply(formatar_percentual_br)
                        
                        df_para_ia = df_filtrado.copy()
                        df_para_ia["Preco_Unitario"] = df_para_ia["Preco_Unitario"].apply(formatar_moeda_br)
                        df_para_ia["Faturamento_Total"] = df_para_ia["Faturamento_Total"].apply(formatar_moeda_br)
                        
                        contexto_metricas = (
                            f"\n\n[DADOS OFICIAIS PRÉ-FORMATADOS]:\n"
                            f"- Período Oficial: Janeiro a Dezembro de 2024\n"
                            f"- Faturamento Total: {formatar_moeda_br(total_faturamento)}\n"
                            f"- Quantidade Total Vendida: {total_quantidade:,} unidades\n"
                            f"- Ticket Médio Global: {formatar_moeda_br(ticket_medio)}\n\n"
                            f"Resumo Oficial por Categoria:\n{resumo_categorias_fmt.to_string(index=False)}\n"
                        )
                        
                        response = client.chat.completions.create(
                            model="openai/gpt-oss-safeguard-20b",
                            messages=[
                                {"role": "system", "content": PROMPTS_SISTEMA[tom_relatorio]},
                                {"role": "user", "content": f"Elabore o relatório utilizando EXATAMENTE os valores monetários pré-formatados. Regra: Ao criar tabelas em Markdown, alinhe a 1ª coluna à esquerda e colunas numéricas à direita usando '---:'.\n\n{contexto_metricas}\n\nDados detalhados:\n{df_para_ia.to_csv(index=False)}"}
                            ],
                        )
                        relatorio_ia = response.choices[0].message.content
                        
                        # --- LIMPEZA DE TEXTO (Palavras grudadas e Cifrão) ---
                        relatorio_ia = re.sub(r'([a-zA-ZáéíóúãõçÁÉÍÓÚÃÕÇ])(\d\.)', r'\1\n\n\2', relatorio_ia)
                        
                        # Dicionário de desgrude bruto
                        substituicoes = {
                            "MonitoresePeriféricos": "Monitores e Periféricos",
                            "Recomenda-se": "Recomenda-se ",
                            "Periféricosdomina": "Periféricos domina",
                            "enquantoMonitores": "enquanto Monitores",
                            "OMonitor": "O Monitor",
                            "Wirelesse": "Wireless e",
                            "e oHub": "e o Hub",
                            "dePeriféricos": "de Periféricos",
                            "médio médio": "médio"
                        }
                        for errado, certo in substituicoes.items():
                            relatorio_ia = relatorio_ia.replace(errado, certo)
                        
                        # Força o cifrão limpo e perfeito no texto oficial (para PDF e Exportação)
                        relatorio_ia = re.sub(r'\bR\s+([\d]{1,3}(?:\.[\d]{3})*,\d{2})', r'R$ \1', relatorio_ia)
                        relatorio_ia = relatorio_ia.replace("R$ R$", "R$").replace("R$$", "R$")
                        
                        relatorio_ia = relatorio_ia.replace(r'\*\*', '**')
                        relatorio_ia = re.sub(r'\*\*\s+(.*?)\s+\*\*', r'**\1**', relatorio_ia)
                        relatorio_ia = re.sub(r'`([^`]+)`', r'**\1**', relatorio_ia)
                        
                        relatorio_ia = (
                            relatorio_ia.replace("up-selling", "vendas adicionais").replace("upselling", "vendas adicionais")
                                        .replace("Upselling", "Vendas Adicionais").replace("Rato", "Mouse")
                                        .replace("audio", "áudio").replace("Audio", "Áudio")
                                        .replace("video", "vídeo").replace("Video", "Vídeo")
                        )
                        
                        st.session_state["relatorio_atual"] = relatorio_ia
                        st.session_state["df_processado"] = df_filtrado
                        
                        with open("relatorio_executivo.md", "w", encoding="utf-8") as f:
                            f.write(f"# Relatório Executivo ({tom_relatorio} - {categoria_selecionada})\n\n{relatorio_ia}")
                    st.success("🎉 Análise avançada gerada com sucesso e pronta para revisão!")

            if "relatorio_atual" in st.session_state:
                st.divider()
                st.markdown("## 🔍 Pré-visualização e Validação Visual")
                aba_texto, aba_graficos = st.tabs(["📄 Relatório Estratégico (Markdown)", "📈 Gráficos Analíticos Avançados"])
                
                with aba_texto:
                    st.info(f"Modo Ativo: **{tom_relatorio}** | Filtro Aplicado: **{categoria_selecionada}**")
                    # O TRUQUE DE MESTRE CONTRA O BUG DO LATEX NA WEB
                    # Aplicamos o escape apenas na string que vai para a tela, preservando a variável original
                    texto_web = st.session_state["relatorio_atual"].replace("R$", r"R\$")
                    st.markdown(texto_web)
                    
                with aba_graficos:
                    st.markdown("#### Análise Gráfica Comparativa de Desempenho")
                    renderizar_graficos_analiticos(st.session_state["df_processado"])
                
                st.divider()
                st.markdown("## 📥 Exportação de Resultados Profissionais")
                
                df_excel = st.session_state["df_processado"]
                excel_bytes = gerar_excel_executivo(df_excel, total_faturamento, total_quantidade, ticket_medio)
                pdf_bytes = gerar_pdf_executivo(st.session_state["relatorio_atual"], categoria_selecionada, tom_relatorio)

                zip_output = io.BytesIO()
                with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.writestr("relatorio_executivo.md", st.session_state["relatorio_atual"])
                    zipf.writestr("relatorio_vendas_executivo.xlsx", excel_bytes)
                    zipf.writestr("relatorio_executivo.pdf", pdf_bytes)
                zip_bytes = zip_output.getvalue()

                col_down1, col_down2, col_down3, col_down4 = st.columns(4)
                with col_down1: st.download_button("📄 Markdown", st.session_state["relatorio_atual"], "relatorio_executivo.md", "text/markdown", use_container_width=True)
                with col_down2: st.download_button("📊 Excel", excel_bytes, "relatorio_vendas_executivo.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                with col_down3: st.download_button("📑 PDF", pdf_bytes, "relatorio_executivo.pdf", "application/pdf", use_container_width=True)
                with col_down4: st.download_button("📦 Pacote ZIP", zip_bytes, "pacote_relatorio_executivo.zip", "application/zip", use_container_width=True)
                    
    except Exception as e:
        st.error(f"❌ Ocorreu um erro ao processar o ficheiro: {e}")