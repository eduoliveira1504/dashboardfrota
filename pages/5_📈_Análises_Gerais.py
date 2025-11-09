import streamlit as st
import pandas as pd
import plotly.express as px
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import load_all_data, check_data_loaded, apply_filters, ui_view_mode, render_kpis, section_advanced, insights_gerais, render_insights

st.set_page_config(page_title="Análises Gerais", page_icon="📈", layout="wide")
st.title("📈 Análises Gerais")

check_data_loaded()

df_viagens, *_ = load_all_data(st.session_state['uploaded_file'])
df_filtrado = apply_filters(df_viagens)
view_mode = ui_view_mode()

if not df_filtrado.empty:
    
    # ========== COMPARAÇÃO MOTORISTAS ==========
    st.subheader("👥 Comparação entre Motoristas")
    
    df_mot = df_filtrado.groupby('MOTORISTA').agg({
        'ID_VIAGEM': 'count',
        'KM_TOTAL_PERCORRIDO': 'sum',
        'TOTAL_KM/LITRO': 'mean',
        'GASTO_FINAL_TOTAL': 'sum'
    }).reset_index()
    df_mot.columns = ['Motorista', 'Viagens', 'KM', 'KM/L', 'Custo']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.bar(df_mot, x='Motorista', y='KM', 
                     title="KM por Motorista", color='KM')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.bar(df_mot, x='Motorista', y='KM/L', 
                     title="Eficiência por Motorista", color='KM/L')
        st.plotly_chart(fig2, use_container_width=True)
    
    # ========== COMPARAÇÃO VEÍCULOS ==========
    st.subheader("🚙 Comparação entre Veículos")
    
    df_veic = df_filtrado.groupby('MODELO_VEICULO').agg({
        'ID_VIAGEM': 'count',
        'KM_TOTAL_PERCORRIDO': 'sum',
        'GASTO_FINAL_TOTAL': 'sum'
    }).reset_index()
    df_veic.columns = ['Veículo', 'Viagens', 'KM', 'Custo']
    
    fig3 = px.pie(df_veic, values='KM', names='Veículo', 
                  title="Distribuição de KM por Veículo")
    st.plotly_chart(fig3, use_container_width=True)
    
    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📊 Evolução Temporal")
            df_tempo = df_filtrado.groupby(
                df_filtrado['DATA_INICIO_VIAGEM'].dt.to_period('M')
            ).agg({'KM_TOTAL_PERCORRIDO': 'sum', 'GASTO_FINAL_TOTAL': 'sum'}).reset_index()
            df_tempo['DATA_INICIO_VIAGEM'] = df_tempo['DATA_INICIO_VIAGEM'].astype(str)
            
            fig4 = px.line(df_tempo, x='DATA_INICIO_VIAGEM', y='KM_TOTAL_PERCORRIDO',
                          markers=True, title="KM ao longo do tempo")
            st.plotly_chart(fig4, use_container_width=True)
    
    # ========== INSIGHTS ==========
    render_insights(insights_gerais(df_filtrado))

else:
    st.warning("⚠️ Nenhum dado disponível.")
