import streamlit as st
import pandas as pd
import plotly.express as px
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import load_all_data, check_data_loaded, apply_filters, ui_view_mode, render_kpis, section_advanced, insights_cidade, render_insights

st.set_page_config(page_title="Por Cidade", page_icon="🏙️", layout="wide")
st.title("🏙️ Análise por Cidade")

check_data_loaded()

df_viagens, *_ = load_all_data(st.session_state['uploaded_file'])
df_filtrado = apply_filters(df_viagens)
view_mode = ui_view_mode()

if not df_filtrado.empty:
    
    # Preparar dados de cidades
    cidades_data = []
    for _, viagem in df_filtrado.iterrows():
        if pd.notna(viagem['CIDADE_DE_PARTIDA']):
            cidades_data.append({
                'cidade': viagem['CIDADE_DE_PARTIDA'],
                'km': viagem['KM_TOTAL_PERCORRIDO'],
                'combustivel': viagem['CUSTO_TOTAL_COMBUSTIVEL'],
                'dias': viagem['DIAS_TOTAL_VIAGEM']
            })
        
        for i in range(1, 5):
            col = f'CIDADE_DE_DESTINO_{i}'
            if col in viagem.index and pd.notna(viagem[col]):
                cidades_data.append({
                    'cidade': viagem[col],
                    'km': viagem['KM_TOTAL_PERCORRIDO'],
                    'combustivel': viagem['CUSTO_TOTAL_COMBUSTIVEL'],
                    'dias': viagem['DIAS_TOTAL_VIAGEM']
                })
    
    df_cidades = pd.DataFrame(cidades_data)
    df_cidades_agg = df_cidades.groupby('cidade').agg({
        'km': 'sum',
        'combustivel': 'sum',
        'dias': 'sum'
    }).reset_index()
    df_cidades_agg.columns = ['Cidade', 'KM Total', 'Custo Combustível', 'Dias Total']
    df_cidades_agg['Visitas'] = df_cidades.groupby('cidade').size().values
    df_cidades_agg = df_cidades_agg.sort_values('KM Total', ascending=False)
    
    # ========== KPIs ==========
    render_kpis([
        {"label": "🏙️ Cidades", "value": f"{len(df_cidades_agg)}"},
        {"label": "🏆 Mais Visitada", "value": df_cidades_agg.iloc[0]['Cidade']},
        {"label": "📏 Maior KM", "value": df_cidades_agg.iloc[0]['Cidade']},
        {"label": "💰 Maior Gasto", "value": df_cidades_agg.sort_values('Custo Combustível', ascending=False).iloc[0]['Cidade']}
    ])
    
    st.markdown("---")
    
    # ========== GRÁFICO PRINCIPAL ==========
    st.subheader("📊 Top 10 Cidades por KM")
    
    fig = px.bar(
        df_cidades_agg.head(10),
        x='Cidade',
        y='KM Total',
        text='KM Total',
        title="Cidades mais percorridas",
        color='KM Total',
        color_continuous_scale='Blues'
    )
    fig.update_traces(texttemplate='%{text:,.0f} km', textposition='outside')
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== MODO COMPLETO ==========
    if view_mode == "Completo":
        with section_advanced():
            st.subheader("📋 Todas as Cidades")
            st.dataframe(df_cidades_agg, use_container_width=True)
    
    # ========== INSIGHTS ==========
    render_insights(insights_cidade(df_cidades_agg))

else:
    st.warning("⚠️ Nenhum dado disponível.")
