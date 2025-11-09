import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

# ===================== CACHE & CARREGAMENTO =====================

@st.cache_data
def load_all_data(uploaded_file):
    """Carrega todas as abas do Excel"""
    try:
        df_viagens = pd.read_excel(uploaded_file, sheet_name='DADOS_VIAGEM')
        df_abastecimentos = pd.read_excel(uploaded_file, sheet_name='ABASTECIMENTOS')
        df_avarias = pd.read_excel(uploaded_file, sheet_name='AVARIAS_VIAGEM')
        df_hospedagens = pd.read_excel(uploaded_file, sheet_name='HOSPEDAGENS')
        df_frota = pd.read_excel(uploaded_file, sheet_name='FROTA')
        df_manutencoes = pd.read_excel(uploaded_file, sheet_name='DESPESAS_MANUTENCOES')
        
        # Converter datas
        df_viagens['DATA_INICIO_VIAGEM'] = pd.to_datetime(df_viagens['DATA_INICIO_VIAGEM'])
        df_viagens['DATA_RETORNO'] = pd.to_datetime(df_viagens['DATA_RETORNO'])
        
        if not df_abastecimentos.empty:
            df_abastecimentos['DATA_ABASTECIMENTO'] = pd.to_datetime(
                df_abastecimentos['DATA_ABASTECIMENTO'], errors='coerce'
            )
        
        if not df_manutencoes.empty:
            df_manutencoes['DATA_REVISAO'] = pd.to_datetime(
                df_manutencoes['DATA_REVISAO'], errors='coerce'
            )
        
        return df_viagens, df_abastecimentos, df_avarias, df_hospedagens, df_frota, df_manutencoes
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return None, None, None, None, None, None


# ===================== FILTROS =====================

def apply_filters(df_viagens):
    """Aplica filtros na sidebar"""
    st.sidebar.header("🔍 Filtros")
    
    st.sidebar.subheader("📅 Período")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        data_inicio = st.date_input(
            "Início",
            value=df_viagens['DATA_INICIO_VIAGEM'].min(),
            key="data_inicio"
        )
    
    with col2:
        data_fim = st.date_input(
            "Fim",
            value=df_viagens['DATA_RETORNO'].max(),
            key="data_fim"
        )
    
    motoristas = ['Todos'] + sorted(df_viagens['MOTORISTA'].dropna().unique().tolist())
    motorista = st.sidebar.selectbox("👤 Motorista", motoristas)
    
    veiculos = ['Todos'] + sorted(df_viagens['MODELO_VEICULO'].dropna().unique().tolist())
    veiculo = st.sidebar.selectbox("🚗 Veículo", veiculos)
    
    # Aplicar filtros
    df = df_viagens.copy()
    df = df[(df['DATA_INICIO_VIAGEM'] >= pd.to_datetime(data_inicio)) & 
            (df['DATA_RETORNO'] <= pd.to_datetime(data_fim))]
    
    if motorista != 'Todos':
        df = df[df['MOTORISTA'] == motorista]
    
    if veiculo != 'Todos':
        df = df[df['MODELO_VEICULO'] == veiculo]
    
    st.sidebar.info(f"📊 **{len(df)}** viagens")
    
    return df


def check_data_loaded():
    """Verifica se arquivo foi carregado"""
    if 'uploaded_file' not in st.session_state:
        st.warning("⚠️ Nenhum arquivo carregado. Volte à página inicial.")
        st.stop()


# ===================== UI HELPERS =====================

def ui_view_mode():
    """Seletor de modo de visualização"""
    st.sidebar.markdown("---")
    return st.sidebar.radio(
        "🧭 Modo de visualização",
        ["Essencial", "Completo"],
        help="Essencial: resumo. Completo: detalhes avançados."
    )


def render_kpis(kpis):
    """Renderiza cards de KPIs"""
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        col.metric(
            label=kpi["label"],
            value=kpi["value"],
            delta=kpi.get("delta"),
            help=kpi.get("help")
        )


def section_advanced(title="🔬 Análises Detalhadas"):
    """Cria expander para seção avançada"""
    return st.expander(title, expanded=False)


# ===================== FORMATAÇÃO =====================

def fmt_money(v):
    """R$ 1.234,56"""
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_num(v):
    """1.234"""
    return f"{v:,.0f}".replace(",", ".")

def fmt_float(v, decimals=2):
    """12.34"""
    return f"{v:.{decimals}f}"


# ===================== GEOLOCALIZAÇÃO =====================

@st.cache_data(ttl=86400)  # Cache por 24h
def geocode_cidade(cidade, uf=None):
    """Obtém coordenadas (lat, lon) de uma cidade"""
    if pd.isna(cidade) or cidade == '':
        return None, None
    
    try:
        geolocator = Nominatim(user_agent="dashboard_frota", timeout=10)
        
        if uf and not pd.isna(uf):
            location = geolocator.geocode(f"{cidade}, {uf}, Brasil")
        else:
            location = geolocator.geocode(f"{cidade}, Brasil")
        
        if location:
            return location.latitude, location.longitude
        
        location = geolocator.geocode(f"{cidade}, Brasil")
        if location:
            return location.latitude, location.longitude
        
        return None, None
    
    except (GeocoderTimedOut, GeocoderServiceError):
        time.sleep(1)
        return None, None
    except Exception:
        return None, None


def get_viagens_com_coords(df_viagens):
    """Adiciona coordenadas às viagens - VERSÃO CORRIGIDA"""
    df = df_viagens.copy()
    
    # Verificar se há dados
    if df.empty:
        return df, {}
    
    # Lista de cidades únicas
    cidades_unicas = set()
    
    # Coletar cidades de todas as viagens
    for _, row in df.iterrows():
        # Origem
        if pd.notna(row.get('CIDADE_DE_PARTIDA')):
            uf = row.get('UF_PARTIDA') if 'UF_PARTIDA' in df.columns else None
            cidades_unicas.add((row['CIDADE_DE_PARTIDA'], uf))
        
        # Destinos (1 a 4)
        for i in range(1, 5):
            col_cidade = f'CIDADE_DE_DESTINO_{i}'
            col_uf = f'UF_DESTINO_{i}'
            if col_cidade in df.columns and pd.notna(row.get(col_cidade)):
                uf = row.get(col_uf) if col_uf in df.columns else None
                cidades_unicas.add((row[col_cidade], uf))
    
    # Geocodificar cidades únicas
    coords_cache = {}
    for cidade, uf in cidades_unicas:
        if cidade and cidade not in coords_cache:
            lat, lon = geocode_cidade(cidade, uf)
            coords_cache[cidade] = (lat, lon)
    
    # Adicionar coordenadas ao dataframe
    df['lat_origem'] = df['CIDADE_DE_PARTIDA'].map(
        lambda x: coords_cache.get(x, (None, None))[0] if pd.notna(x) else None
    )
    df['lon_origem'] = df['CIDADE_DE_PARTIDA'].map(
        lambda x: coords_cache.get(x, (None, None))[1] if pd.notna(x) else None
    )
    
    df['lat_destino'] = df['CIDADE_DE_DESTINO_1'].map(
        lambda x: coords_cache.get(x, (None, None))[0] if pd.notna(x) else None
    )
    df['lon_destino'] = df['CIDADE_DE_DESTINO_1'].map(
        lambda x: coords_cache.get(x, (None, None))[1] if pd.notna(x) else None
    )
    
    return df, coords_cache


# ===================== ROTEAMENTO REAL =====================

try:
    import openrouteservice as ors
    ORS_AVAILABLE = True
except ImportError:
    ORS_AVAILABLE = False


@st.cache_data(ttl=86400)
def get_rota_real(lat_origem, lon_origem, lat_destino, lon_destino, api_key):
    """Obtém rota real pelas rodovias"""
    if not ORS_AVAILABLE:
        return [(lat_origem, lon_origem), (lat_destino, lon_destino)], None, None
    
    try:
        client = ors.Client(key=api_key)
        
        coords = [
            [lon_origem, lat_origem],
            [lon_destino, lat_destino]
        ]
        
        route = client.directions(
            coordinates=coords,
            profile='driving-hgv',
            format='geojson',
            validate=False,
            preference='recommended'
        )
        
        geometry = route['features'][0]['geometry']['coordinates']
        rota_coords = [(coord[1], coord[0]) for coord in geometry]
        
        properties = route['features'][0]['properties']
        distancia_real = properties['segments'][0]['distance'] / 1000
        tempo_estimado = properties['segments'][0]['duration'] / 3600
        
        return rota_coords, distancia_real, tempo_estimado
    
    except Exception:
        return [(lat_origem, lon_origem), (lat_destino, lon_destino)], None, None


# ===================== INSIGHTS =====================

def insights_gerais(df):
    """Calcula insights gerais da frota"""
    if df is None or df.empty:
        return []
    
    insights = []
    
    try:
        row = df.loc[df['TOTAL_KM/LITRO'].idxmax()]
        insights.append({
            "icon": "⛽",
            "title": "Melhor Eficiência",
            "desc": f"Viagem #{int(row['ID_VIAGEM'])} com {fmt_float(row['TOTAL_KM/LITRO'])} km/L",
            "extra": f"Motorista: {row['MOTORISTA']}"
        })
    except:
        pass
    
    try:
        tmp = df[df['KM_TOTAL_PERCORRIDO'] > 0].copy()
        tmp['custo_km'] = tmp['GASTO_FINAL_TOTAL'] / tmp['KM_TOTAL_PERCORRIDO']
        row = tmp.loc[tmp['custo_km'].idxmin()]
        insights.append({
            "icon": "💰",
            "title": "Menor Custo/KM",
            "desc": f"{fmt_money(row['custo_km'])}/km na viagem #{int(row['ID_VIAGEM'])}",
            "extra": f"Motorista: {row['MOTORISTA']}"
        })
    except:
        pass
    
    try:
        row = df.loc[df['KM_TOTAL_PERCORRIDO'].idxmax()]
        insights.append({
            "icon": "🚀",
            "title": "Maior Viagem",
            "desc": f"{fmt_num(row['KM_TOTAL_PERCORRIDO'])} km percorridos",
            "extra": f"{row['CIDADE_DE_PARTIDA']} → {row.get('CIDADE_DE_DESTINO_1', '?')}"
        })
    except:
        pass
    
    try:
        row = df.loc[df['DIAS_TOTAL_VIAGEM'].idxmax()]
        insights.append({
            "icon": "📆",
            "title": "Viagem Mais Longa",
            "desc": f"{fmt_float(row['DIAS_TOTAL_VIAGEM'], 0)} dias",
            "extra": f"Motorista: {row['MOTORISTA']}"
        })
    except:
        pass
    
    return insights


def insights_motorista(df):
    """Insights específicos de um motorista"""
    if df is None or df.empty:
        return []
    
    insights = []
    
    insights.append({
        "icon": "⛽",
        "title": "Eficiência Média",
        "desc": f"{fmt_float(df['TOTAL_KM/LITRO'].mean())} km/L",
        "extra": f"Baseado em {len(df)} viagens"
    })
    
    insights.append({
        "icon": "📆",
        "title": "Duração Média",
        "desc": f"{fmt_float(df['DIAS_TOTAL_VIAGEM'].mean(), 1)} dias/viagem",
        "extra": f"Total: {fmt_float(df['DIAS_TOTAL_VIAGEM'].sum(), 0)} dias"
    })
    
    try:
        row = df.loc[df['GASTO_FINAL_TOTAL'].idxmax()]
        insights.append({
            "icon": "💸",
            "title": "Viagem Mais Cara",
            "desc": f"{fmt_money(row['GASTO_FINAL_TOTAL'])}",
            "extra": f"Viagem #{int(row['ID_VIAGEM'])} • {fmt_num(row['KM_TOTAL_PERCORRIDO'])} km"
        })
    except:
        pass
    
    insights.append({
        "icon": "💰",
        "title": "Custo Médio/Viagem",
        "desc": f"{fmt_money(df['GASTO_FINAL_TOTAL'].mean())}",
        "extra": f"Total gasto: {fmt_money(df['GASTO_FINAL_TOTAL'].sum())}"
    })
    
    return insights


def insights_veiculo(df):
    """Insights de um veículo"""
    if df is None or df.empty:
        return []
    
    insights = []
    
    insights.append({
        "icon": "⚡",
        "title": "Eficiência Média",
        "desc": f"{fmt_float(df['TOTAL_KM/LITRO'].mean())} km/L",
        "extra": f"Melhor: {fmt_float(df['TOTAL_KM/LITRO'].max())} km/L"
    })
    
    insights.append({
        "icon": "🛢️",
        "title": "Consumo Total",
        "desc": f"{fmt_num(df['TOTAL_LITROS_DIESEL'].sum())} litros",
        "extra": f"Em {len(df)} viagens"
    })
    
    try:
        row = df.loc[df['KM_TOTAL_PERCORRIDO'].idxmax()]
        insights.append({
            "icon": "📏",
            "title": "Maior Percurso",
            "desc": f"{fmt_num(row['KM_TOTAL_PERCORRIDO'])} km",
            "extra": f"Viagem #{int(row['ID_VIAGEM'])} com {row['MOTORISTA']}"
        })
    except:
        pass
    
    insights.append({
        "icon": "💰",
        "title": "Custo Total",
        "desc": f"{fmt_money(df['GASTO_FINAL_TOTAL'].sum())}",
        "extra": f"Custo/KM: {fmt_money(df['GASTO_FINAL_TOTAL'].sum() / df['KM_TOTAL_PERCORRIDO'].sum())}"
    })
    
    return insights


def insights_cidade(df_cidades):
    """Insights de cidades"""
    if df_cidades is None or df_cidades.empty:
        return []
    
    insights = []
    
    top_km = df_cidades.sort_values('KM Total', ascending=False).iloc[0]
    insights.append({
        "icon": "📍",
        "title": "Maior KM Percorrido",
        "desc": f"{top_km['Cidade']}",
        "extra": f"{fmt_num(top_km['KM Total'])} km"
    })
    
    top_vis = df_cidades.sort_values('Visitas', ascending=False).iloc[0]
    insights.append({
        "icon": "🧭",
        "title": "Mais Visitada",
        "desc": f"{top_vis['Cidade']}",
        "extra": f"{fmt_num(top_vis['Visitas'])} visitas"
    })
    
    top_custo = df_cidades.sort_values('Custo Combustível', ascending=False).iloc[0]
    insights.append({
        "icon": "💰",
        "title": "Maior Gasto",
        "desc": f"{top_custo['Cidade']}",
        "extra": f"{fmt_money(top_custo['Custo Combustível'])}"
    })
    
    return insights


def render_insights(insights, title="💡 Insights e Estatísticas"):
    """Renderiza seção de insights"""
    st.markdown("---")
    st.subheader(title)
    
    if not insights:
        st.info("Sem insights para o filtro atual.")
        return
    
    cols = st.columns(2)
    for i, insight in enumerate(insights):
        with cols[i % 2]:
            st.success(f"""
**{insight['icon']} {insight['title']}**  
{insight['desc']}  
_{insight.get('extra', '')}_
            """)
