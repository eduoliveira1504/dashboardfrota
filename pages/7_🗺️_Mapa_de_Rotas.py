import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import os, sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import (load_all_data, check_data_loaded, apply_filters, ui_view_mode, 
                   render_kpis, section_advanced, get_viagens_com_coords, 
                   get_rota_real)

st.set_page_config(page_title="Mapa de Rotas", page_icon="🗺️", layout="wide")
st.title("🗺️ Mapa de Rotas da Frota")

check_data_loaded()

# ============= CONFIGURAÇÃO DA API =============
st.sidebar.markdown("---")
st.sidebar.subheader("🛣️ Rotas Reais")

api_key = st.sidebar.text_input(
    "OpenRouteService API Key",
    type="password",
    help="Cole sua API Key para ver rotas reais nas rodovias"
)

usar_rotas_reais = st.sidebar.checkbox(
    "Usar rotas reais",
    value=bool(api_key),
    disabled=not api_key,
    help="Ative para calcular rotas pelas rodovias (BR-116, etc.)"
)

if usar_rotas_reais and api_key:
    st.sidebar.success("✅ Rotas reais ativadas!")
    st.sidebar.caption("🚛 Rotas calculadas para caminhões")
    
    # Botão para limpar cache de rotas
    if st.sidebar.button("🔄 Recalcular Rotas"):
        if 'rotas_trechos' in st.session_state:
            del st.session_state['rotas_trechos']
        if 'mapa_processado' in st.session_state:
            st.session_state['mapa_processado'] = False
        st.rerun()
else:
    st.sidebar.info("ℹ️ Usando linhas retas")
    if not api_key:
        st.sidebar.caption("👉 [Obter API Key grátis](https://openrouteservice.org/dev/#/signup)")

# Carregar e filtrar dados
df_viagens, *_ = load_all_data(st.session_state['uploaded_file'])
df_filtrado = apply_filters(df_viagens)
view_mode = ui_view_mode()

st.info("""
**🗺️ Visualização Geográfica das Rotas**  
Este mapa mostra **todas as rotas e paradas** da frota. Com API Key, você vê as rotas reais pelas rodovias!
""")

if not df_filtrado.empty:
    
    # Criar chave única para o estado atual
    filtro_key = f"{len(df_filtrado)}_{df_filtrado['ID_VIAGEM'].min()}_{df_filtrado['ID_VIAGEM'].max()}_{usar_rotas_reais}"
    
    if 'mapa_filtro_key' not in st.session_state or st.session_state['mapa_filtro_key'] != filtro_key:
        st.session_state['mapa_filtro_key'] = filtro_key
        st.session_state['mapa_processado'] = False
        if 'rotas_trechos' in st.session_state:
            del st.session_state['rotas_trechos']
    
    # Geocodificar viagens
    if not st.session_state.get('mapa_processado', False):
        with st.spinner("📍 Carregando coordenadas das cidades..."):
            df_com_coords, coords_cache = get_viagens_com_coords(df_filtrado)
            st.session_state['df_com_coords'] = df_com_coords
            st.session_state['coords_cache'] = coords_cache
            st.session_state['mapa_processado'] = True
    else:
        df_com_coords = st.session_state['df_com_coords']
        coords_cache = st.session_state['coords_cache']
    
    df_mapa = df_com_coords.dropna(subset=['lat_origem', 'lon_origem', 'lat_destino', 'lon_destino'])
    
    if not df_mapa.empty:
        
        # ========== KPIs ==========
        total_cidades = len(coords_cache)
        total_rotas = len(df_mapa)
        km_total = df_mapa['KM_TOTAL_PERCORRIDO'].sum()
        
        kpis = [
            {"label": "🏙️ Cidades", "value": f"{total_cidades}", "help": "Cidades mapeadas"},
            {"label": "🛣️ Viagens", "value": f"{total_rotas}", "help": "Viagens no mapa"},
            {"label": "📏 KM Registrado", "value": f"{km_total:,.0f} km", "help": "KM dos dados"},
            {"label": "🚚 Total Viagens", "value": f"{len(df_filtrado)}", "help": "Todas as viagens"}
        ]
        
        render_kpis(kpis)
        
        st.markdown("---")
        
        # ========== MAPA PRINCIPAL ==========
        st.subheader("🗺️ Mapa Interativo com Todas as Rotas")
        
        center_lat = float(df_mapa[['lat_origem', 'lat_destino']].mean().mean())
        center_lon = float(df_mapa[['lon_origem', 'lon_destino']].mean().mean())
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=5,
            tiles='OpenStreetMap'
        )
        
        # Contador de visitas por cidade (considerando TODAS as paradas)
        visitas_por_cidade = {}
        for cidade in coords_cache.keys():
            count = 0
            for _, viagem in df_mapa.iterrows():
                # Contar origem
                if viagem['CIDADE_DE_PARTIDA'] == cidade:
                    count += 1
                # Contar todos os destinos
                for i in range(1, 5):
                    col = f'CIDADE_DE_DESTINO_{i}'
                    if col in viagem.index and viagem[col] == cidade:
                        count += 1
            visitas_por_cidade[cidade] = count
        
        # Marcadores das cidades
        for cidade, (lat, lon) in coords_cache.items():
            if lat and lon:
                visitas = visitas_por_cidade.get(cidade, 0)
                
                if visitas > 0:  # Só mostrar cidades com visitas
                    radius = float(5 + (visitas * 2))
                    
                    folium.CircleMarker(
                        location=[float(lat), float(lon)],
                        radius=radius,
                        popup=folium.Popup(f"<b>{cidade}</b><br>{visitas} visitas", max_width=200),
                        tooltip=str(cidade),
                        color='#1f77b4',
                        fill=True,
                        fillColor='#1f77b4',
                        fillOpacity=0.6
                    ).add_to(m)
        
        # Cores para motoristas
        motoristas_unicos = df_mapa['MOTORISTA'].unique().tolist()
        cores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F38181', '#AA96DA', '#95E1D3']
        cores_motoristas = {
            motorista: cores[i % len(cores)] 
            for i, motorista in enumerate(motoristas_unicos)
        }
        
        # ========== ADICIONAR ROTAS (COM MÚLTIPLAS PARADAS) ==========
        total_trechos = 0
        
        for idx, viagem in df_mapa.iterrows():
            cor = cores_motoristas.get(viagem['MOTORISTA'], '#1f77b4')
            
            id_viagem = int(viagem['ID_VIAGEM'])
            motorista = str(viagem['MOTORISTA'])
            veiculo = str(viagem['MODELO_VEICULO'])
            km_registrado = float(viagem['KM_TOTAL_PERCORRIDO'])
            custo = float(viagem['GASTO_FINAL_TOTAL'])
            km_l = float(viagem['TOTAL_KM/LITRO'])
            
            # ========== CONSTRUIR SEQUÊNCIA DE PARADAS ==========
            paradas = []
            
            # Adicionar origem
            if pd.notna(viagem['lat_origem']) and pd.notna(viagem['lon_origem']):
                paradas.append({
                    'nome': str(viagem['CIDADE_DE_PARTIDA']),
                    'lat': float(viagem['lat_origem']),
                    'lon': float(viagem['lon_origem'])
                })
            
            # Adicionar todos os destinos (1, 2, 3, 4)
            for i in range(1, 5):
                col_cidade = f'CIDADE_DE_DESTINO_{i}'
                if col_cidade in viagem.index and pd.notna(viagem[col_cidade]):
                    cidade = str(viagem[col_cidade])
                    if cidade in coords_cache:
                        lat, lon = coords_cache[cidade]
                        if lat and lon:
                            paradas.append({
                                'nome': cidade,
                                'lat': float(lat),
                                'lon': float(lon)
                            })
            
            # Se não tem paradas suficientes, pular
            if len(paradas) < 2:
                continue
            
            # Construir string da rota completa
            rota_completa = ' → '.join([p['nome'] for p in paradas])
            
            # ========== TRAÇAR ROTAS ENTRE CADA PAR DE PARADAS ==========
            distancia_total_real = 0
            tempo_total_real = 0
            trechos_calculados = 0
            
            for i in range(len(paradas) - 1):
                origem = paradas[i]
                destino = paradas[i + 1]
                total_trechos += 1
                
                # Determinar se usar rota real ou linha reta
                if usar_rotas_reais and api_key:
                    # Gerar ID único para este trecho
                    trecho_id = f"{id_viagem}_{i}"
                    
                    # Verificar se já calculamos este trecho
                    if 'rotas_trechos' not in st.session_state:
                        st.session_state['rotas_trechos'] = {}
                    
                    if trecho_id in st.session_state['rotas_trechos']:
                        trecho_info = st.session_state['rotas_trechos'][trecho_id]
                        rota_coords = trecho_info['coords']
                        dist_trecho = trecho_info['distancia']
                        tempo_trecho = trecho_info['tempo']
                    else:
                        # Calcular rota real para este trecho
                        with st.spinner(f"🚛 Calculando trecho {i+1}/{len(paradas)-1} da viagem #{id_viagem}..."):
                            rota_coords, dist_trecho, tempo_trecho = get_rota_real(
                                origem['lat'], origem['lon'],
                                destino['lat'], destino['lon'],
                                api_key
                            )
                        
                        # Salvar no cache de trechos
                        st.session_state['rotas_trechos'][trecho_id] = {
                            'coords': rota_coords,
                            'distancia': dist_trecho,
                            'tempo': tempo_trecho
                        }
                    
                    tipo_rota = "🛣️ Rota real pelas rodovias"
                    weight = 3
                    
                    if dist_trecho:
                        distancia_total_real += dist_trecho
                        tempo_total_real += tempo_trecho if tempo_trecho else 0
                        trechos_calculados += 1
                else:
                    # Linha reta
                    rota_coords = [(origem['lat'], origem['lon']), (destino['lat'], destino['lon'])]
                    dist_trecho = None
                    tipo_rota = "📏 Linha reta"
                    weight = 2
                
                # ========== POPUP COM INFORMAÇÕES ==========
                popup_html = f"""
                <div style="font-family: Arial; font-size: 12px; min-width: 300px;">
                    <b style="font-size: 14px; color: {cor};">Viagem #{id_viagem}</b><br>
                    <hr style="margin: 5px 0;">
                    <b>🛣️ Tipo:</b> {tipo_rota}<br>
                    <b>👤 Motorista:</b> {motorista}<br>
                    <b>🚗 Veículo:</b> {veiculo}<br>
                    <hr style="margin: 5px 0;">
                    <b>📍 Rota Completa ({len(paradas)} paradas):</b><br>
                    <i style="font-size: 11px;">{rota_completa}</i><br>
                    <hr style="margin: 5px 0;">
                    <b>🎯 Trecho Atual ({i+1}/{len(paradas)-1}):</b><br>
                    <span style="color: {cor};">⬤</span> {origem['nome']} → {destino['nome']}<br>
                """
                
                if dist_trecho:
                    popup_html += f"""
                    <b>📏 Distância do trecho:</b> {dist_trecho:.0f} km<br>
                    <b>⏱️ Tempo do trecho:</b> {tempo_trecho:.1f}h<br>
                    """
                
                popup_html += f"""
                    <hr style="margin: 5px 0;">
                    <b>📊 Total da Viagem Completa:</b><br>
                    <b>KM Registrado:</b> {km_registrado:,.0f} km<br>
                """
                
                if trechos_calculados > 0:
                    diferenca = distancia_total_real - km_registrado
                    cor_diff = "green" if abs(diferenca) < 50 else "orange" if abs(diferenca) < 100 else "red"
                    popup_html += f"""
                    <b>🛣️ KM Real (calculado):</b> {distancia_total_real:,.0f} km<br>
                    <b>📊 Diferença:</b> <span style="color: {cor_diff};">{diferenca:+.0f} km</span><br>
                    <b>⏱️ Tempo Total Estimado:</b> {tempo_total_real:.1f}h<br>
                    """
                
                popup_html += f"""
                    <b>💰 Custo Total:</b> R$ {custo:,.2f}<br>
                    <b>⛽ KM/L:</b> {km_l:.2f}<br>
                </div>
                """
                
                # ========== DESENHAR LINHA DA ROTA ==========
                folium.PolyLine(
                    locations=rota_coords,
                    color=cor,
                    weight=weight,
                    opacity=0.7,
                    popup=folium.Popup(popup_html, max_width=400),
                    tooltip=f"Viagem #{id_viagem}: {origem['nome']} → {destino['nome']}"
                ).add_to(m)
        
        # Legenda
        legenda_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; 
                    background-color: white; 
                    border: 2px solid grey; 
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 14px;
                    z-index: 9999;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
            <b>🚗 Motoristas ({len(cores_motoristas)})</b><br>
        '''
        for motorista, cor in cores_motoristas.items():
            legenda_html += f'<span style="color: {cor}; font-size: 18px;">●</span> {motorista}<br>'
        
        legenda_html += '<hr style="margin: 5px 0;">'
        legenda_html += f'<b>📊 Estatísticas:</b><br>'
        legenda_html += f'Trechos totais: {total_trechos}<br>'
        
        if usar_rotas_reais:
            legenda_html += f'<span style="color: green;">🛣️</span> Rotas reais ativas<br>'
        else:
            legenda_html += f'<span style="color: gray;">📏</span> Linhas retas<br>'
        
        legenda_html += '</div>'
        
        m.get_root().html.add_child(folium.Element(legenda_html))
        
        # Renderizar
        st_folium(m, width=None, height=600, returned_objects=[], key="mapa_rotas")
        
        st.markdown("---")
        if usar_rotas_reais:
            st.success(f"🛣️ **{total_trechos} trechos** mapeados com rotas reais! Clique nas linhas para detalhes.")
        else:
            st.caption("💡 **Dica:** Configure a API Key na sidebar para ver rotas reais nas rodovias com múltiplas paradas!")
        
        # ========== PREPARAR DADOS DE ANÁLISE (ANTES DO MODO COMPLETO) ==========
        paradas_por_viagem = []
        for _, viagem in df_mapa.iterrows():
            num_paradas = 1  # Origem
            for i in range(1, 5):
                col = f'CIDADE_DE_DESTINO_{i}'
                if col in viagem.index and pd.notna(viagem[col]):
                    num_paradas += 1
            
            paradas_por_viagem.append({
                'ID': int(viagem['ID_VIAGEM']),
                'Motorista': viagem['MOTORISTA'],
                'Paradas': num_paradas,
                'KM': float(viagem['KM_TOTAL_PERCORRIDO'])
            })
        
                # ========== MODO COMPLETO ==========
        if view_mode == "Completo":
            with section_advanced():
                
                st.subheader("🏙️ Ranking de Cidades por Visitas")
                
                # Criar tabela de cidades
                df_cidades_rank = pd.DataFrame([
                    {'Cidade': cidade, 'Visitas': visitas}
                    for cidade, visitas in visitas_por_cidade.items()
                    if visitas > 0
                ]).sort_values('Visitas', ascending=False)
                
                # Adicionar informações extras se disponível
                if not df_cidades_rank.empty:
                    # Adicionar coluna de ranking
                    df_cidades_rank.insert(0, 'Ranking', range(1, len(df_cidades_rank) + 1))
                    
                    st.dataframe(
                        df_cidades_rank,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Ranking": st.column_config.NumberColumn(
                                "🏆 Ranking",
                                help="Posição no ranking de visitas"
                            ),
                            "Cidade": st.column_config.TextColumn(
                                "🏙️ Cidade",
                                help="Nome da cidade"
                            ),
                            "Visitas": st.column_config.NumberColumn(
                                "📊 Visitas",
                                help="Número total de visitas (origem + destinos)"
                            )
                        }
                    )
                    
                    # Estatísticas rápidas abaixo da tabela
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "🥇 Cidade Líder",
                            df_cidades_rank.iloc[0]['Cidade'],
                            f"{df_cidades_rank.iloc[0]['Visitas']} visitas"
                        )
                    
                    with col2:
                        total_visitas = df_cidades_rank['Visitas'].sum()
                        st.metric(
                            "📍 Total de Visitas",
                            f"{total_visitas}",
                            f"{len(df_cidades_rank)} cidades"
                        )
                    
                    with col3:
                        media_visitas = df_cidades_rank['Visitas'].mean()
                        st.metric(
                            "📊 Média de Visitas",
                            f"{media_visitas:.1f}",
                            "por cidade"
                        )

        
        # ========== INSIGHTS ==========
        st.markdown("---")
        st.subheader("💡 Insights Geográficos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cidade mais visitada
            if visitas_por_cidade:
                cidade_top = max(visitas_por_cidade, key=visitas_por_cidade.get)
                st.info(f"""
**🏙️ Cidade Mais Visitada**  
{cidade_top}  
_{visitas_por_cidade[cidade_top]} visitas (todas as paradas)_
                """)
            
            # Viagem com mais paradas
            if paradas_por_viagem:
                viagem_mais_paradas = max(paradas_por_viagem, key=lambda x: x['Paradas'])
                st.success(f"""
**🛣️ Viagem com Mais Paradas**  
Viagem #{viagem_mais_paradas['ID']}  
_{viagem_mais_paradas['Paradas']} paradas • {viagem_mais_paradas['KM']:,.0f} km_
                """)
        
        with col2:
            # Média de paradas
            if paradas_por_viagem:
                media_paradas = sum(p['Paradas'] for p in paradas_por_viagem) / len(paradas_por_viagem)
                st.info(f"""
**📊 Média de Paradas**  
{media_paradas:.1f} paradas/viagem  
_Total: {total_trechos} trechos mapeados_
                """)
            
            # Total de cidades únicas
            cidades_com_visitas = sum(1 for v in visitas_por_cidade.values() if v > 0)
            st.success(f"""
**🌍 Alcance Geográfico**  
{total_cidades} cidades diferentes  
_{cidades_com_visitas} com visitas registradas_
            """)
    
    else:
        st.warning("⚠️ Não foi possível obter coordenadas para as cidades.")
        
        st.info("""
**💡 Dica:** Certifique-se de que os nomes das cidades estão corretos.

**Cidades encontradas nos dados:**
        """)
        
        cidades_origem = df_filtrado['CIDADE_DE_PARTIDA'].dropna().unique()
        st.write(", ".join(sorted(cidades_origem[:10])))

else:
    st.warning("⚠️ Nenhum dado disponível com os filtros aplicados.")
