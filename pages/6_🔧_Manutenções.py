import streamlit as st
import pandas as pd
import plotly.express as px
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import load_all_data, check_data_loaded, ui_view_mode, render_kpis, section_advanced, render_insights

st.set_page_config(page_title="Manutenções", page_icon="🔧", layout="wide")
st.title("🔧 Despesas com Manutenções")

check_data_loaded()

# Carregar dados
df_viagens, *_, df_manut = load_all_data(st.session_state['uploaded_file'])

# ========== FILTROS CUSTOMIZADOS PARA MANUTENÇÕES ==========
st.sidebar.header("🔍 Filtros")
st.sidebar.subheader("📅 Período")

col1, col2 = st.sidebar.columns(2)

with col1:
    data_inicio = st.date_input(
        "Início",
        value=df_viagens['DATA_INICIO_VIAGEM'].min(),
        key="data_inicio_manut"
    )

with col2:
    data_fim = st.date_input(
        "Fim",
        value=df_viagens['DATA_RETORNO'].max(),
        key="data_fim_manut"
    )

# Filtro de veículo (baseado em manutenções, não em viagens)
if df_manut is not None and not df_manut.empty:
    veiculos_manut = ['Todos'] + sorted(df_manut['VEICULO - PLACA'].dropna().unique().tolist())
    veiculo_selecionado = st.sidebar.selectbox("🚗 Veículo", veiculos_manut, key="veiculo_manut")
else:
    veiculo_selecionado = 'Todos'

view_mode = ui_view_mode()

if df_manut is not None and not df_manut.empty:
    
    # Aplicar filtros
    df_manut_filt = df_manut[
        (df_manut['DATA_REVISAO'] >= pd.to_datetime(data_inicio)) &
        (df_manut['DATA_REVISAO'] <= pd.to_datetime(data_fim))
    ]
    
    # Filtro por veículo
    if veiculo_selecionado != 'Todos':
        df_manut_filt = df_manut_filt[df_manut_filt['VEICULO - PLACA'] == veiculo_selecionado]
    
    st.sidebar.info(f"📊 **{len(df_manut_filt)}** manutenções")
    
    if not df_manut_filt.empty:
        
        # ========== KPIs ==========
        render_kpis([
            {"label": "🔧 Manutenções", "value": f"{len(df_manut_filt)}"},
            {"label": "💰 Custo Total", "value": f"R$ {df_manut_filt['VALOR'].sum():,.2f}"},
            {"label": "📊 Custo Médio", "value": f"R$ {df_manut_filt['VALOR'].mean():,.2f}"},
            {"label": "🚗 Veículos", "value": f"{df_manut_filt['VEICULO - PLACA'].nunique()}"}
        ])
        
        st.markdown("---")
        
        # ========== GRÁFICO PRINCIPAL ==========
        st.subheader("💰 Custos por Veículo")
        
        df_veic_manut = df_manut_filt.groupby('VEICULO - PLACA').agg({
            'VALOR': ['sum', 'count']
        }).reset_index()
        df_veic_manut.columns = ['Veículo', 'Custo', 'Quantidade']
        df_veic_manut = df_veic_manut.sort_values('Custo', ascending=False)
        
        fig = px.bar(
            df_veic_manut.head(10),
            x='Veículo',
            y='Custo',
            text='Custo',
            title="Top 10 Veículos - Maiores Custos de Manutenção",
            color='Custo',
            color_continuous_scale='Reds'
        )
        fig.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # ========== MODO COMPLETO ==========
        if view_mode == "Completo":
            with section_advanced():
                st.subheader("📋 Histórico Completo de Manutenções")
                st.dataframe(
                    df_manut_filt[['DATA_REVISAO', 'VEICULO - PLACA', 'ITENS', 'VALOR', 'RESPONSAVEL_DESPESA']]
                    .sort_values('DATA_REVISAO', ascending=False),
                    use_container_width=True
                )
        
        # ========== INSIGHTS ==========
        st.markdown("---")
        st.subheader("💡 Insights de Manutenções")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Maior gasto
            row = df_manut_filt.loc[df_manut_filt['VALOR'].idxmax()]
            st.success(f"""
**💸 Maior Gasto Individual**  
R$ {row['VALOR']:,.2f}  
_{row['VEICULO - PLACA']} • {row['ITENS'][:50]}..._
            """)
            
            # Veículo com mais manutenções
            top_veic = df_veic_manut.iloc[0]
            st.info(f"""
**🔧 Veículo com Mais Manutenções**  
{top_veic['Veículo']}  
_{int(top_veic['Quantidade'])} manutenções • R$ {top_veic['Custo']:,.2f}_
            """)
        
        with col2:
            # Custo médio
            st.info(f"""
**📊 Custo Médio**  
R$ {df_manut_filt['VALOR'].mean():,.2f}  
_por manutenção no período_
            """)
            
            # Total e veículos únicos
            st.success(f"""
**🚗 Veículos Atendidos**  
{df_manut_filt['VEICULO - PLACA'].nunique()} veículos  
_{len(df_manut_filt)} manutenções realizadas_
            """)
    
    else:
        st.info("ℹ️ Nenhuma manutenção no período filtrado.")

else:
    st.info("ℹ️ Nenhum dado de manutenção disponível.")
