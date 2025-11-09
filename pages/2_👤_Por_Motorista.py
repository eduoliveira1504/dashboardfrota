import streamlit as st
import pandas as pd
import plotly.express as px
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import load_all_data, check_data_loaded, apply_filters, ui_view_mode, render_kpis, section_advanced, insights_motorista, render_insights

st.set_page_config(page_title="Por Motorista", page_icon="👤", layout="wide")
st.title("👤 Análise por Motorista")

check_data_loaded()

df_viagens, *_ = load_all_data(st.session_state['uploaded_file'])
df_filtrado = apply_filters(df_viagens)
view_mode = ui_view_mode()

if not df_filtrado.empty:
    
    # Seleção de motorista
    motoristas = sorted(df_filtrado['MOTORISTA'].dropna().unique().tolist())
    motorista = st.selectbox("🔍 Selecione o motorista:", motoristas)
    
    df_mot = df_filtrado[df_filtrado['MOTORISTA'] == motorista]
    
    # ========== KPIs ==========
    render_kpis([
        {"label": "🚚 Viagens", "value": f"{len(df_mot)}"},
        {"label": "📏 KM Total", "value": f"{df_mot['KM_TOTAL_PERCORRIDO'].sum():,.0f} km"},
        {"label": "⛽ KM/L Médio", "value": f"{df_mot['TOTAL_KM/LITRO'].mean():.2f}"},
        {"label": "💰 Custo Total", "value": f"R$ {df_mot['GASTO_FINAL_TOTAL'].sum():,.2f}"}
    ])
    
    st.markdown("---")
    
    # ========== GRÁFICO PRINCIPAL ==========
    st.subheader("⛽ Eficiência por Viagem")
    
    fig = px.bar(
        df_mot,
        x='ID_VIAGEM',
        y='TOTAL_KM/LITRO',
        hover_data=['CIDADE_DE_DESTINO_1', 'KM_TOTAL_PERCORRIDO'],
        title=f"KM/L em cada viagem — {motorista}",
        color='TOTAL_KM/LITRO',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📋 Histórico Completo")
            
            st.dataframe(
                df_mot[['ID_VIAGEM', 'DATA_INICIO_VIAGEM', 'DATA_RETORNO', 
                       'CIDADE_DE_PARTIDA', 'CIDADE_DE_DESTINO_1',
                       'KM_TOTAL_PERCORRIDO', 'TOTAL_KM/LITRO', 'GASTO_FINAL_TOTAL']]
                .sort_values('DATA_INICIO_VIAGEM', ascending=False),
                use_container_width=True
            )
    
    # ========== INSIGHTS ==========
    render_insights(insights_motorista(df_mot))

else:
    st.warning("⚠️ Nenhum dado disponível.")
