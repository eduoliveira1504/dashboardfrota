# 🚚 Dashboard de Gestão de Frota

Dashboard interativo desenvolvido com Streamlit para análise completa de viagens, custos e performance de frotas de transporte.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎯 Funcionalidades

### 📊 Análises Disponíveis

- **Números Gerais**: KPIs consolidados da frota (viagens, KM, custos, eficiência)
- **Por Motorista**: Performance individual de cada condutor
- **Por Veículo**: Utilização, aproveitamento e custos por veículo
- **Por Cidade**: Análise de destinos e rotas mais utilizadas
- **Análises Gerais**: Comparativos entre motoristas e veículos
- **Manutenções**: Controle de custos de manutenção por veículo
- **Mapa de Rotas**: Visualização geográfica com rotas reais pelas rodovias

### 🗺️ Mapa Interativo

- Geocodificação automática de cidades
- Rotas reais calculadas pelas rodovias brasileiras (OpenRouteService API)
- Visualização de múltiplas paradas por viagem
- Marcadores proporcionais ao número de visitas
- Popups com informações detalhadas de cada viagem

### 💡 Insights Automáticos

Cada página gera insights automáticos baseados nos dados filtrados:
- Melhor eficiência (KM/L)
- Menor custo por quilômetro
- Viagens mais longas
- Cidades mais visitadas
- E muito mais!

## 🛠️ Tecnologias

- **Python 3.9+**
- **Streamlit**: Framework para dashboards
- **Pandas**: Manipulação de dados
- **Plotly**: Gráficos interativos
- **Folium**: Mapas interativos
- **OpenRouteService**: Roteamento real nas rodovias
- **Geopy**: Geocodificação de cidades

## 👤 Autor

**Seu Nome**

- LinkedIn: [Eduardo Pereira](https://www.linkedin.com/in/eduardo-oliveira-pereira/)
- GitHub: [@eduoliveira1504](https://github.com/eduoliveira1504)

## 🙏 Agradecimentos

- [Streamlit](https://streamlit.io/) pelo framework incrível
- [OpenRouteService](https://openrouteservice.org/) pela API de roteamento
- Comunidade Python pelos ótimos pacotes

---

⭐ Se este projeto foi útil, considere dar uma estrela!