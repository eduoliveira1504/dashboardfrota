import streamlit as st
import pandas as pd

# ============= CONFIGURAÇÃO DA PÁGINA =============
st.set_page_config(
    page_title="Dashboard de Frota",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS minimalista e clean
# st.markdown("""
#     <style>
#     .big-title {
#         font-size: 3.5rem;
#         font-weight: 700;
#         color: #1f77b4;
#         text-align: center;
#         margin-bottom: 0.5rem;
#         margin-top: 2rem;
#     }
#     .subtitle {
#         font-size: 1.3rem;
#         text-align: center;
#         color: #666;
#         margin-bottom: 3rem;
#         font-weight: 300;
#     }
#     .welcome-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 2rem;
#         border-radius: 1rem;
#         color: white;
#         text-align: center;
#         margin: 2rem 0;
#     }
#     .step-card {
#         background-color: #f8f9fa;
#         padding: 1.5rem;
#         border-radius: 0.8rem;
#         border-left: 4px solid #1f77b4;
#         margin: 1rem 0;
#     }
#     </style>
# """, unsafe_allow_html=True)

# ============= SIDEBAR - UPLOAD =============
st.sidebar.title("📁 Carregar Dados")

uploaded_file = st.sidebar.file_uploader(
    "Selecione o arquivo Excel",
    type=['xlsx', 'xls'],
    help="Formato: CONSOLIDADO_DESPESAS.xlsx"
)

# Salvar no session_state
if uploaded_file is not None:
    st.session_state['uploaded_file'] = uploaded_file
    st.sidebar.success("✅ Arquivo carregado!")
else:
    if 'uploaded_file' in st.session_state:
        del st.session_state['uploaded_file']

st.sidebar.markdown("---")
st.sidebar.info("**Dashboard v2.0**\nSimplificado & Intuitivo")

# ============= CONTEÚDO PRINCIPAL =============

# Título principal
st.markdown('<h1 class="big-title">🚚 Dashboard de Frota</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Gestão inteligente de viagens e custos</p>', unsafe_allow_html=True)

# Se arquivo foi carregado
if 'uploaded_file' in st.session_state:
    
    # Card de boas-vindas
    st.markdown("""
        <div class="welcome-card">
            <h2>🎉 Dados carregados com sucesso!</h2>
            <p>Use o menu lateral para navegar pelas análises</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Preview rápido dos dados
    try:
        df_viagens = pd.read_excel(st.session_state['uploaded_file'], sheet_name='DADOS_VIAGEM')
        df_viagens['DATA_INICIO_VIAGEM'] = pd.to_datetime(df_viagens['DATA_INICIO_VIAGEM'])
        df_viagens['DATA_RETORNO'] = pd.to_datetime(df_viagens['DATA_RETORNO'])
        
        st.markdown("### 📊 Resumo Rápido")
        
        # KPIs em cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🚚 Viagens", 
                f"{len(df_viagens)}",
                help="Total de viagens registradas"
            )
        
        with col2:
            st.metric(
                "📏 KM Total", 
                f"{df_viagens['KM_TOTAL_PERCORRIDO'].sum():,.0f} km",
                help="Quilometragem total"
            )
        
        with col3:
            st.metric(
                "💰 Despesas", 
                f"R$ {df_viagens['GASTO_FINAL_TOTAL'].sum():,.2f}",
                help="Gastos totais"
            )
        
        with col4:
            st.metric(
                "⛽ KM/L", 
                f"{df_viagens['TOTAL_KM/LITRO'].mean():.2f}",
                help="Eficiência média"
            )
        
        # Informações do período
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
**📅 Período dos dados**  
{df_viagens['DATA_INICIO_VIAGEM'].min().strftime('%d/%m/%Y')} até {df_viagens['DATA_RETORNO'].max().strftime('%d/%m/%Y')}
            """)
        
        with col2:
            motoristas = df_viagens['MOTORISTA'].nunique()
            veiculos = df_viagens['MODELO_VEICULO'].nunique()
            st.info(f"""
**🔢 Recursos**  
{motoristas} Motoristas • {veiculos} Veículos
            """)
        
        # Call to action
        st.markdown("---")
        st.success("👈 **Navegue pelas páginas** no menu lateral para análises detalhadas!")
        
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {e}")

# Se nenhum arquivo foi carregado
else:
    
    # Instruções simples
    st.markdown("### 🚀 Como começar")
    
    st.markdown("""
    <div class="step-card">
        <h4>1️⃣ Carregue seu arquivo</h4>
        <p>Use o botão <strong>📁 Carregar Dados</strong> na barra lateral</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <h4>2️⃣ Explore as análises</h4>
        <p>Navegue pelas páginas no menu lateral para visualizar:</p>
        <ul>
            <li><strong>📊 Números Gerais</strong> — Visão consolidada</li>
            <li><strong>👤 Por Motorista</strong> — Performance individual</li>
            <li><strong>🚙 Por Veículo</strong> — Utilização da frota</li>
            <li><strong>🏙️ Por Cidade</strong> — Rotas e destinos</li>
            <li><strong>📈 Análises Gerais</strong> — Comparativos</li>
            <li><strong>🔧 Manutenções</strong> — Controle de custos</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="step-card">
        <h4>3️⃣ Aplique filtros</h4>
        <p>Use os filtros na barra lateral para focar em períodos, motoristas ou veículos específicos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Exemplo visual
    st.markdown("---")
    st.markdown("### 📸 Preview do Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**📊 KPIs Visuais**\nMétricas principais em destaque")
    
    with col2:
        st.info("**📈 Gráficos Interativos**\nVisualizações dinâmicas")
    
    with col3:
        st.info("**💡 Insights**\nEstatísticas automáticas")

# ============= RODAPÉ =============
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 2rem 0 1rem 0;'>
    <p style='margin: 0;'><strong>Dashboard de Gestão de Frota v2.0</strong></p>
    <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem;'>
        Desenvolvido com Streamlit • Pandas • Plotly
    </p>
</div>
""", unsafe_allow_html=True)
