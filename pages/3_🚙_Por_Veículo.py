import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import load_all_data, check_data_loaded, apply_filters, ui_view_mode, render_kpis, section_advanced, insights_veiculo, render_insights

st.set_page_config(page_title="Por Veículo", page_icon="🚙", layout="wide")
st.title("🚙 Análise por Veículo")

check_data_loaded()

df_viagens, *_ = load_all_data(st.session_state['uploaded_file'])
df_filtrado = apply_filters(df_viagens)
view_mode = ui_view_mode()

if not df_filtrado.empty:
    
    veiculos = sorted(df_filtrado['MODELO_VEICULO'].dropna().unique().tolist())
    veiculo = st.selectbox("🔍 Selecione o veículo:", veiculos)
    
    df_veic = df_filtrado[df_filtrado['MODELO_VEICULO'] == veiculo]
    
    # ========== KPIs ==========
    render_kpis([
        {"label": "🚚 Viagens", "value": f"{len(df_veic)}"},
        {"label": "📏 KM Total", "value": f"{df_veic['KM_TOTAL_PERCORRIDO'].sum():,.0f} km"},
        {"label": "⛽ KM/L Médio", "value": f"{df_veic['TOTAL_KM/LITRO'].mean():.2f}"},
        {"label": "💰 Custo Total", "value": f"R$ {df_veic['GASTO_FINAL_TOTAL'].sum():,.2f}"}
    ])
    
    st.markdown("---")
    
    # ========== ÍNDICE DE APROVEITAMENTO ==========
    st.subheader("📈 Índice de Aproveitamento")
    
    dias_totais = (df_veic['DATA_RETORNO'].max() - df_veic['DATA_INICIO_VIAGEM'].min()).days
    dias_prod = df_veic['DIAS_TOTAL_VIAGEM'].sum()
    aproveit = (dias_prod / dias_totais * 100) if dias_totais > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 Dias Produtivos", f"{dias_prod:.0f}")
    col2.metric("📅 Dias Disponíveis", f"{dias_totais}")
    col3.metric("📊 Aproveitamento", f"{aproveit:.1f}%", 
                delta="Meta: 75%" if aproveit >= 75 else "Abaixo da meta")
    
    # Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aproveit,
        title={'text': "Aproveitamento (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 75], 'color': "yellow"},
                {'range': [75, 100], 'color': "lightgreen"}
            ]
        }
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📋 Histórico de Viagens")
            st.dataframe(
                df_veic[['ID_VIAGEM', 'DATA_INICIO_VIAGEM', 'MOTORISTA', 
                        'KM_TOTAL_PERCORRIDO', 'TOTAL_KM/LITRO', 'GASTO_FINAL_TOTAL']]
                .sort_values('DATA_INICIO_VIAGEM', ascending=False),
                use_container_width=True
            )
    
    # ========== INSIGHTS ==========
    render_insights(insights_veiculo(df_veic))

else:
    st.warning("⚠️ Nenhum dado disponível.")
