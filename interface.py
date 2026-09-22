import os
import io
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

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
    /* Estilo global e fontes */
    .main {
        background-color: #0E1117;
    }
    
    /* Cartões de Métricas (KPIs) com efeito moderno */
    .metric-card {
        background: linear-gradient(135deg, #1E2530 0%, #13171F 100%);
        border: 1px solid #2A3441;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        text-align: center;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        border-color: #3B82F6;
        transform: translateY(-2px);
    }
    
    /* Títulos de secção personalizados */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Divisores elegantes */
    hr {
        margin: 1.5rem 0;
        border-color: #2A3441;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO DA APLICAÇÃO ---
col_head1, col_head2 = st.columns([0.85, 0.15])
with col_head1:
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
    ["Executivo (Padrão)", "Comercial / Foco em Vendas", "Técnico / Foco em Custos"]
)

# Gestão de estado para mudança de tom
if "tom_anterior" not in st.session_state:
    st.session_state["tom_anterior"] = tom_relatorio

if st.session_state["tom_anterior"] != tom_relatorio:
    st.session_state["tom_anterior"] = tom_relatorio
    if "relatorio_atual" in st.session_state:
        del st.session_state["relatorio_atual"]

prompts_sistema = {
    "Executivo (Padrão)": "Você é um analista de dados sénior especialista em relatórios executivos de alto impacto.",
    "Comercial / Foco em Vendas": "Você é um diretor comercial focado em estratégias de vendas, expansão de mercado e aumento de receita.",
    "Técnico / Foco em Custos": "Você é um auditor financeiro e de operações focado em otimização de stock, margens e redução de custos."
}

st.sidebar.divider()
st.sidebar.markdown("#### 📁 Histórico de Sessão")
if os.path.exists("relatorio_executivo.md"):
    if st.sidebar.button("📂 Ver Último Relatório Guardado", use_container_width=True):
        with open("relatorio_executivo.md", "r", encoding="utf-8") as f:
            conteudo_historico = f.read()
        st.sidebar.markdown(conteudo_historico)
else:
    st.sidebar.info("Nenhum relatório anterior guardado.")

# --- CORPO PRINCIPAL: IMPORTAÇÃO DE DADOS ---
st.markdown("### 📥 Importação de Ficheiro de Dados")
ficheiro_carregado = st.file_uploader("Arraste ou selecione o seu ficheiro CSV (colunas obrigatórias: Produto, Categoria, Preco_Unitario, Quantidade_Vendida)", type=["csv"])

if ficheiro_carregado is not None:
    try:
        # Lê o CSV enviado
        df = pd.read_csv(ficheiro_carregado)
        
        # Validação robusta de colunas obrigatórias
        colunas_obrigatorias = ["Produto", "Categoria", "Preco_Unitario", "Quantidade_Vendida"]
        colunas_em_falta = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_em_falta:
            st.error(f"❌ Erro de Validação: O ficheiro não contém as colunas obrigatórias: {colunas_em_falta}")
        else:
            # Processamento base do faturamento
            df["Faturamento_Total"] = df["Preco_Unitario"] * df["Quantidade_Vendida"]
            
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
                        system_prompt = prompts_sistema[tom_relatorio]
                        
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
                        col_g1, col_g2 = st.columns(2)
                        with col_g1:
                            st.markdown("**Faturamento por Produto (R$)**")
                            st.bar_chart(df_graf.set_index("Produto")["Faturamento_Total"], color="#3B82F6")
                        with col_g2:
                            st.markdown("**Volume Vendido por Produto (Unidades)**")
                            st.bar_chart(df_graf.set_index("Produto")["Quantidade_Vendida"], color="#10B981")
                
                st.divider()
                st.markdown("## 📥 Exportação de Resultados Profissionais")
                
                col_down1, col_down2 = st.columns(2)
                
                with col_down1:
                    st.download_button(
                        label="📄 Descarregar Relatório em Markdown (.md)",
                        data=st.session_state["relatorio_atual"],
                        file_name="relatorio_executivo.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                with col_down2:
                    df_excel = st.session_state["df_processado"]
                    output = io.BytesIO()
                    
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = "Relatório Executivo"
                    ws.views.sheetView[0].showGridLines = True
                    
                    headers = list(df_excel.columns)
                    ws.append(headers)
                    
                    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                    data_font = Font(name="Calibri", size=11)
                    total_font = Font(name="Calibri", size=11, bold=True)
                    
                    thin_border = Border(
                        left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
                        top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
                    )
                    total_border = Border(top=Side(style='thin', color='000000'), bottom=Side(style='double', color='000000'))
                    
                    for col_num in range(1, len(headers) + 1):
                        cell = ws.cell(row=1, column=col_num)
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    
                    for row_idx, row in enumerate(df_excel.values, start=2):
                        ws.append(list(row))
                        for col_idx in range(1, len(row) + 1):
                            cell = ws.cell(row=row_idx, column=col_idx)
                            cell.font = data_font
                            cell.border = thin_border
                            if headers[col_idx - 1] in ["Preco_Unitario", "Faturamento_Total"]:
                                cell.number_format = '"R$ "* #,##0.00'
                                cell.alignment = Alignment(horizontal="right")
                            elif headers[col_idx - 1] == "Quantidade_Vendida":
                                cell.number_format = '#,##0'
                                cell.alignment = Alignment(horizontal="center")
                            else:
                                cell.alignment = Alignment(horizontal="left")
                    
                    last_row = len(df_excel) + 1
                    total_row_idx = last_row + 1
                    ws.cell(row=total_row_idx, column=1, value="TOTAL")
                    ws.cell(row=total_row_idx, column=4, value=f"=SUM(D2:D{last_row})")
                    ws.cell(row=total_row_idx, column=5, value=f"=SUM(E2:E{last_row})")
                    
                    for col_idx in range(1, len(headers) + 1):
                        cell = ws.cell(row=total_row_idx, column=col_idx)
                        cell.font = total_font
                        cell.border = total_border
                        if headers[col_idx - 1] in ["Preco_Unitario", "Faturamento_Total"]:
                            cell.number_format = '"R$ "* #,##0.00'
                            cell.alignment = Alignment(horizontal="right")
                        elif headers[col_idx - 1] == "Quantidade_Vendida":
                            cell.number_format = '#,##0'
                            cell.alignment = Alignment(horizontal="center")
                    
                    for col in ws.columns:
                        max_len = max(len(str(cell.value or '')) for cell in col)
                        col_letter = get_column_letter(col[0].column)
                        ws.column_dimensions[col_letter].width = max(max_len + 4, 15)
                    
                    wb.save(output)
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        label="📊 Descarregar Relatório Excel Profissional (.xlsx)",
                        data=excel_data,
                        file_name="relatorio_vendas_profissional.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
    except Exception as e:
        st.error(f"❌ Ocorreu um erro ao processar o ficheiro: {e}")