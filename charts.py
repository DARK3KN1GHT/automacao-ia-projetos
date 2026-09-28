import streamlit as st

def renderizar_graficos_analiticos(df_graf):
    """
    Renderiza os gráficos avançados e consolidados de faturamento e volume.
    Isolado da interface principal para cumprir a Clean Architecture.
    """
    if "Produto" in df_graf.columns:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**Faturamento por Produto (R$)**")
            st.bar_chart(df_graf.set_index("Produto")["Faturamento_Total"], color="#3B82F6")
        with col_g2:
            st.markdown("**Volume Vendido por Produto (Unidades)**")
            st.bar_chart(df_graf.set_index("Produto")["Quantidade_Vendida"], color="#10B981")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("#### 📊 Distribuição Consolidada de Faturamento por Categoria")
        df_categoria = df_graf.groupby("Categoria")["Faturamento_Total"].sum()
        st.bar_chart(df_categoria, color="#8B5CF6")