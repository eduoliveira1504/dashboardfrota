import streamlit as st
import pandas as pd
import plotly.express as px
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import load_all_data, check_data_loaded, apply_filters, ui_view_mode, render_kpis, section_advanced, insights_gerais, render_insights

st.set_page_config(page_title="Números Gerais", page_icon="📊", layout="wide")
st.title("📊 Números Gerais da Frota")

check_data_loaded()

# Carregar e filtrar dados
df_viagens, df_abast, df_avarias, df_hosp, df_frota, df_manut = load_all_data(st.session_state['uploaded_file'])
df_filtrado = apply_filters(df_viagens)
view_mode = ui_view_mode()

if not df_filtrado.empty:
    
    # ========== KPIs ESSENCIAIS ====s======
    total_viagens = len(df_filtrado)
    km_total = df_filtrado['KM_TOTAL_PERCORRIDO'].sum()
    custo_total = df_filtrado['GASTO_FINAL_TOTAL'].sum()
    km_l_medio = df_filtrado['TOTAL_KM/LITRO'].mean()
    
    render_kpis([
        {"label": "🚚 Total de Viagens", "value": f"{total_viagens}", "help": "Viagens no período"},
        {"label": "📏 KM Total", "value": f"{km_total:,.0f} km", "help": "Quilometragem total"},
        {"label": "💰 Despesas Totais", "value": f"R$ {custo_total:,.2f}", "help": "Todas as despesas"},
        {"label": "⛽ KM/L Médio", "value": f"{km_l_medio:.2f}", "help": "Eficiência média"}
    ])
    
    st.markdown("---")
    
    # ========== GRÁFICO PRINCIPAL ==========
    st.subheader("📊 Distribuição de Custos")
    
    custos_df = pd.DataFrame({
        'Categoria': ['Combustível', 'Avarias', 'Hospedagem'],
        'Valor': [
            df_filtrado['CUSTO_TOTAL_COMBUSTIVEL'].sum(),
            df_filtrado['CUSTO_TOTAL_AVARIAS'].sum(),
            df_filtrado['CUSTO_TOTAL_HOSPEDAGEM'].sum()
        ]
    })
    
    fig = px.pie(
        custos_df,
        values='Valor',
        names='Categoria',
        title="Como o dinheiro foi gasto",
        hole=0.4,
        color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📋 Resumo por Motorista")
            
            df_mot = df_filtrado.groupby('MOTORISTA').agg({
                'ID_VIAGEM': 'count',
                'KM_TOTAL_PERCORRIDO': 'sum',
                'GASTO_FINAL_TOTAL': 'sum',
                'TOTAL_KM/LITRO': 'mean'
            }).reset_index()
            df_mot.columns = ['Motorista', 'Viagens', 'KM', 'Custo', 'KM/L']
            
            st.dataframe(df_mot, use_container_width=True)
            
            st.subheader("🚙 Resumo por Veículo")
            
            df_veic = df_filtrado.groupby('MODELO_VEICULO').agg({
                'ID_VIAGEM': 'count',
                'KM_TOTAL_PERCORRIDO': 'sum',
                'GASTO_FINAL_TOTAL': 'sum',
                'TOTAL_KM/LITRO': 'mean'
            }).reset_index()
            df_veic.columns = ['Veículo', 'Viagens', 'KM', 'Custo', 'KM/L']
            
            st.dataframe(df_veic, use_container_width=True)
    
    # ========== INSIGHTS ==========
    render_insights(insights_gerais(df_filtrado))

else:
    st.warning("⚠️ Nenhum dado com os filtros atuais.")
