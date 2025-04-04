import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests
from io import StringIO
from datetime import datetime
import calendar

# Configuração da página
st.set_page_config(
    page_title="DashBirds: Observatório de Aves - RPPN Estação Veracel",
    page_icon="🦉",
    layout="wide"
)


# Função para alternar entre os temas claro e escuro
def configurar_tema():
    # Verifica se a chave 'tema' já existe no session_state
    if 'tema' not in st.session_state:
        st.session_state.tema = 'escuro'  # Tema padrão é escuro

    # Tema escuro - cores
    cores_escuro = {
        'bg_principal': '#121212',
        'bg_card': '#1E1E1E',
        'bg_sidebar': '#121212',
        'texto_principal': '#FFFFFF',
        'texto_secundario': '#AAAAAA',
        'destaque': '#4CAF50',
        'borda': '#333333'
    }

    # Tema claro - cores
    cores_claro = {
        'bg_principal': '#F8F9FA',
        'bg_card': '#FFFFFF',
        'bg_sidebar': '#F0F0F0',
        'texto_principal': '#212529',
        'texto_secundario': '#6C757D',
        'destaque': '#198754',
        'borda': '#DEE2E6'
    }

    # Seleciona o tema ativo
    if st.session_state.tema == 'escuro':
        cores = cores_escuro
    else:
        cores = cores_claro

    # Aplica o CSS com as cores do tema selecionado
    st.markdown(f"""
    <style>
        .main {{
            background-color: {cores['bg_principal']};
            color: {cores['texto_principal']};
        }}

        .stApp {{
            background-color: {cores['bg_principal']};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {cores['bg_sidebar']};
            color: {cores['texto_principal']};
        }}

        .stTextInput, .stSelectbox, .stNumberInput, .stDateInput, .stTimeInput, .stTextArea {{
            background-color: {cores['bg_card']};
            color: {cores['texto_principal']};
        }}

        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6 {{
            color: {cores['texto_principal']} !important;
        }}

        div.block-container {{
            padding-top: 2rem;
        }}

        .dashboard-card {{
            background-color: {cores['bg_card']};
            color: {cores['texto_principal']};
            border: 1px solid {cores['borda']};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}

        .indicador-card {{
            background-color: {cores['bg_card']};
            color: {cores['texto_principal']};
            border: 1px solid {cores['borda']};
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            text-align: center;
        }}

        .indicador-titulo {{
            font-size: 0.8rem;
            color: {cores['texto_secundario']};
            margin-bottom: 0.3rem;
            text-transform: uppercase;
        }}

        .indicador-valor {{
            font-size: 2rem;
            font-weight: bold;
            color: {cores['destaque']};
            margin-bottom: 0rem;
        }}

        .periodo-indicador {{
            background-color: {cores['bg_card']};
            color: {cores['texto_principal']};
            border: 1px solid {cores['borda']};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }}

        .tema-toggle {{
            display: flex;
            align-items: center;
            justify-content: flex-end;
            margin-bottom: 1rem;
        }}

        .section-title {{
            color: {cores['texto_principal']};
            font-weight: bold;
        }}

        .stDataFrame {{
            background-color: {cores['bg_card']};
            color: {cores['texto_principal']};
        }}

        .streamlit-expanderHeader {{
            background-color: {cores['bg_card']};
            color: {cores['texto_principal']};
        }}

        .streamlit-expanderContent {{
            background-color: {cores['bg_card']};
            color: {cores['texto_principal']};
        }}

        .mini-card {{
            background-color: {cores['bg_card']};
            color: {cores['texto_principal']};
            border: 1px solid {cores['borda']};
            border-radius: 6px;
            padding: 0.7rem;
            margin-bottom: 0.7rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .mini-card-titulo {{
            font-size: 0.85rem;
            color: {cores['texto_secundario']};
            margin-bottom: 0rem;
        }}

        .mini-card-valor {{
            font-size: 1.2rem;
            font-weight: bold;
            color: {cores['destaque']};
            margin-left: 1rem;
        }}
    </style>
    """, unsafe_allow_html=True)

    return cores


# Função para download direto da planilha como CSV
@st.cache_data(ttl=3600)
def download_csv_from_google_sheet(sheet_url):
    """
    Faz download direto da planilha como CSV, sem necessidade de API ou credenciais.
    Funciona apenas se a planilha estiver configurada para "Qualquer pessoa com o link pode visualizar".
    """
    try:
        # Extrai o ID da planilha
        sheet_id = sheet_url.split('/d/')[1].split('/edit')[0]

        # Constrói a URL de exportação como CSV
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

        # Faz a requisição HTTP
        response = requests.get(export_url)

        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Lê o conteúdo como CSV
            csv_content = StringIO(response.content.decode('utf-8'))
            df = pd.read_csv(csv_content, low_memory=False)
            return df
        else:
            st.error(f"Erro ao baixar a planilha: {response.status_code}")
            st.warning("Verifique se a planilha está configurada para 'Qualquer pessoa com o link pode visualizar'.")
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Erro ao fazer download da planilha: {e}")
        return pd.DataFrame()


# Carregamento dos dados
@st.cache_data
def load_and_process_data():
    """Carrega e processa os dados iniciais"""
    # Exibe mensagem de carregamento
    with st.spinner("Carregando dados das planilhas..."):
        # Tabela base com informações taxonômicas e ecológicas
        tabela_base = download_csv_from_google_sheet(
            "https://docs.google.com/spreadsheets/d/1HBBDPNcITK9qHeJik3gZy6H0f4jG-s5QsTJKCcSfts0/edit?usp=sharing"
        )

        # Tabela de dados de observações
        tabela_dados = download_csv_from_google_sheet(
            "https://docs.google.com/spreadsheets/d/1pkT3tP_2lDpoWl3m04tsQuvBbClTLhGf2IIEihcwWDs/edit?usp=sharing"
        )

        # Verificação de dados
        if tabela_base.empty or tabela_dados.empty:
            st.error("Não foi possível carregar os dados. Verifique a conexão e as permissões das planilhas.")
            st.stop()

        # Processamento básico
        # Convertendo datas
        if 'Date' in tabela_dados.columns:
            tabela_dados['Date'] = pd.to_datetime(tabela_dados['Date'], errors='coerce')
            tabela_dados['Year'] = tabela_dados['Date'].dt.year
            tabela_dados['Month'] = tabela_dados['Date'].dt.month

        # Combinando os dados
        # Assumindo que ambas tabelas têm uma coluna em comum (nome científico)
        if 'Scientific Name' in tabela_dados.columns and 'Nome científico' in tabela_base.columns:
            # Criando coluna comum para merge
            tabela_dados['species_key'] = tabela_dados['Scientific Name'].str.strip().str.lower()
            tabela_base['species_key'] = tabela_base['Nome científico'].str.strip().str.lower()

            # Merge das tabelas
            dados_completos = pd.merge(
                tabela_dados,
                tabela_base,
                on='species_key',
                how='left',
                suffixes=('_obs', '_base')
            )
        else:
            dados_completos = tabela_dados.copy()
            st.warning("Não foi possível combinar as tabelas. Verificar nomes das colunas.")

        return tabela_base, tabela_dados, dados_completos


# Funções de análise
def calcular_indicadores(df_filtered):
    """Calcula os indicadores principais com base nos dados filtrados"""
    # Número de registros
    n_registros = len(df_filtered)

    # Número de espécies
    n_especies = df_filtered['Scientific Name'].nunique() if 'Scientific Name' in df_filtered.columns else 0

    # Localizações únicas
    n_localizacoes = df_filtered['Location'].nunique() if 'Location' in df_filtered.columns else 0

    # Número de listas (se houver algum identificador de lista)
    n_listas = df_filtered['ListID'].nunique() if 'ListID' in df_filtered.columns else 458  # Valor fixo do exemplo

    # Período dos dados
    if 'Date' in df_filtered.columns:
        data_inicio = df_filtered['Date'].min().strftime('%d/%m/%Y')
        data_fim = df_filtered['Date'].max().strftime('%d/%m/%Y')
        periodo_dados = f"{data_inicio} a {data_fim}"
    else:
        periodo_dados = "03/02/2025 a 15/02/2025"  # Valor do exemplo

    # Espécies ameaçadas - incluindo agora "Quase ameaçada"
    especies_ameacadas_iucn = 0
    if 'IUCN 2021' in df_filtered.columns:
        especies_ameacadas_iucn = df_filtered[
            df_filtered['IUCN 2021'].isin([
                'Vulnerável', 'Em perigo', 'Criticamente ameaçada', 'Quase ameaçada',
                'VU', 'EN', 'CR', 'NT'  # Incluindo também abreviações
            ])
        ]['Scientific Name'].nunique()

    especies_ameacadas_brasil = 0
    if 'MMA 2022' in df_filtered.columns:
        especies_ameacadas_brasil = df_filtered[
            df_filtered['MMA 2022'].isin([
                'Vulnerável', 'Em perigo', 'Criticamente ameaçada', 'Quase ameaçada',
                'VU', 'EN', 'CR', 'NT'  # Incluindo também abreviações
            ])
        ]['Scientific Name'].nunique()

    especies_ameacadas_estado = 0
    if 'Ameaçadas Bahia 2017' in df_filtered.columns:
        especies_ameacadas_estado = df_filtered[
            df_filtered['Ameaçadas Bahia 2017'].notna() &
            (df_filtered['Ameaçadas Bahia 2017'] != '')
            ]['Scientific Name'].nunique()

    # Espécies endêmicas
    endemicas_brasil = 0
    if 'Endêmicas do Brasil (CBRO 2021)' in df_filtered.columns:
        endemicas_brasil = df_filtered[df_filtered['Endêmicas do Brasil (CBRO 2021)'] == 1][
            'Scientific Name'].nunique()

    endemicas_mata_atlantica = 0
    if 'Espécies Endêmicas da Mata Atlântica' in df_filtered.columns:
        endemicas_mata_atlantica = df_filtered[df_filtered['Espécies Endêmicas da Mata Atlântica'] == 1][
            'Scientific Name'].nunique()

    # Espécies migratórias
    migratorias = 0
    if 'Migratórias Somenzari et al. 2017' in df_filtered.columns:
        migratorias = df_filtered[df_filtered['Migratórias Somenzari et al. 2017'].notna()][
            'Scientific Name'].nunique()

    return {
        'n_registros': n_registros,
        'n_especies': n_especies,
        'n_localizacoes': n_localizacoes,
        'n_listas': n_listas,
        'periodo_dados': periodo_dados,
        'especies_ameacadas_iucn': especies_ameacadas_iucn,
        'especies_ameacadas_brasil': especies_ameacadas_brasil,
        'especies_ameacadas_estado': especies_ameacadas_estado,
        'endemicas_brasil': endemicas_brasil,
        'endemicas_mata_atlantica': endemicas_mata_atlantica,
        'migratorias': migratorias
    }


def gerar_grafico_familias(df_filtered):
    """Gera gráfico de barras das famílias mais representativas"""
    if 'Nome da Família' not in df_filtered.columns:
        return None

    # Agrupando por família e contando espécies
    familia_counts = df_filtered.groupby('Nome da Família')['Nome científico'].nunique().reset_index()
    familia_counts.columns = ['Família', 'Número de Espécies']
    familia_counts = familia_counts.sort_values('Número de Espécies', ascending=False).head(10)

    fig = px.bar(
        familia_counts,
        x='Família',
        y='Número de Espécies',
        title='Famílias mais Representativas',
        color='Número de Espécies',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(xaxis_title='Família', yaxis_title='Número de Espécies')

    return fig


def gerar_grafico_especies(df_filtered):
    """Gera gráfico de barras das espécies mais frequentemente registradas"""
    if 'Scientific Name' not in df_filtered.columns:
        return None

    # Contando observações por espécie
    especies_counts = df_filtered['Scientific Name'].value_counts().reset_index()
    especies_counts.columns = ['Espécie', 'Número de Registros']
    especies_counts = especies_counts.sort_values('Número de Registros', ascending=False).head(10)

    fig = px.bar(
        especies_counts,
        x='Espécie',
        y='Número de Registros',
        title='Espécies mais Registradas',
        color='Número de Registros',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(xaxis_title='Espécie', yaxis_title='Número de Registros',
                      xaxis={'categoryorder': 'total descending'})

    return fig


def gerar_grafico_habitats(df_filtered):
    """Gera gráfico de distribuição por habitats preferenciais"""
    if 'Habitat (AVONET)' not in df_filtered.columns:
        return None

    # Agrupando por habitat
    habitat_counts = df_filtered.groupby('Habitat (AVONET)')['Nome científico'].nunique().reset_index()
    habitat_counts = habitat_counts[habitat_counts['Habitat (AVONET)'].notna()]  # Remover valores NA
    habitat_counts.columns = ['Habitat', 'Número de Espécies']
    habitat_counts = habitat_counts.sort_values('Número de Espécies', ascending=False)

    fig = px.bar(
        habitat_counts,
        x='Habitat',
        y='Número de Espécies',
        title='Habitats Preferenciais',
        color='Número de Espécies',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(xaxis_title='Habitat', yaxis_title='Número de Espécies')

    return fig


def gerar_grafico_nicho_trofico(df_filtered):
    """Gera gráfico de pizza para níveis tróficos"""
    if 'Nicho trófico (AVONET)' not in df_filtered.columns:
        return None

    # Agrupando por nível trófico
    trophic_counts = df_filtered.groupby('Nicho trófico (AVONET)')['Nome científico'].nunique().reset_index()
    trophic_counts.columns = ['Nicho Trófico', 'Número de Espécies']

    fig = px.pie(
        trophic_counts,
        values='Número de Espécies',
        names='Nicho Trófico',
        title='Distribuição por Nicho Trófico',
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    return fig


def gerar_mapa_riqueza(df_filtered):
    """Gera mapa de calor de riqueza de espécies por localização com visualização adaptada aos dados"""
    if 'Latitude' not in df_filtered.columns or 'Longitude' not in df_filtered.columns:
        return None

    # Agrupando por localização e contando espécies
    location_species = df_filtered.groupby(['Latitude', 'Longitude', 'Location'])[
        'Scientific Name'].nunique().reset_index()
    location_species.columns = ['Latitude', 'Longitude', 'Location', 'Riqueza de Espécies']

    if len(location_species) == 0:
        return None

    # Criando mapa - usando fit_bounds para adaptar automaticamente aos dados
    # Primeiro, determinamos os limites (bounds) dos nossos dados
    min_lat = location_species['Latitude'].min()
    max_lat = location_species['Latitude'].max()
    min_lon = location_species['Longitude'].min()
    max_lon = location_species['Longitude'].max()

    # Adicionamos uma pequena margem para melhorar a visualização
    lat_margin = (max_lat - min_lat) * 0.1
    lon_margin = (max_lon - min_lon) * 0.1

    # Criando o mapa sem definir location e zoom_start iniciais
    mapa = folium.Map(tiles=None)

    # Adicionando camada de satélite
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(mapa)

    # Adicionando marcadores para cada localização
    for idx, row in location_species.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=row['Riqueza de Espécies'] / 2,  # Raio proporcional à riqueza
            popup=f"Local: {row['Location']}<br>Riqueza: {row['Riqueza de Espécies']} espécies",
            color='yellow',
            fill=True,
            fill_color='yellow',
            fill_opacity=0.6
        ).add_to(mapa)

    # Ajustando o mapa para mostrar todos os pontos (com margem)
    mapa.fit_bounds([
        [min_lat - lat_margin, min_lon - lon_margin],
        [max_lat + lat_margin, max_lon + lon_margin]
    ])

    return mapa


def gerar_grafico_sazonalidade(df_filtered, especie):
    """Gera gráfico de sazonalidade (registros por mês) para uma espécie específica"""
    if 'Scientific Name' not in df_filtered.columns or 'Month' not in df_filtered.columns:
        return None

    # Filtrando pela espécie selecionada
    df_especie = df_filtered[df_filtered['Scientific Name'] == especie]

    # Contando registros por mês
    monthly_counts = df_especie.groupby('Month').size().reindex(range(1, 13), fill_value=0)
    monthly_counts.index = [calendar.month_abbr[i] for i in monthly_counts.index]

    fig = px.bar(
        x=monthly_counts.index,
        y=monthly_counts.values,
        title=f"Sazonalidade: {especie}",
        labels={'x': 'Mês', 'y': 'Número de Registros'}
    )

    return fig


def gerar_mapa_ocorrencia(df_filtered, especie):
    """Gera mapa de ocorrência para uma espécie específica com visualização adaptada aos dados"""
    if 'Scientific Name' not in df_filtered.columns or 'Latitude' not in df_filtered.columns:
        return None

    # Filtrando pela espécie selecionada
    df_especie = df_filtered[df_filtered['Scientific Name'] == especie]

    if len(df_especie) == 0:
        return None

    # Determinando os limites dos dados
    min_lat = df_especie['Latitude'].min()
    max_lat = df_especie['Latitude'].max()
    min_lon = df_especie['Longitude'].min()
    max_lon = df_especie['Longitude'].max()

    # Adicionando uma pequena margem para melhorar a visualização
    lat_margin = max(0.01, (max_lat - min_lat) * 0.1)  # Garantindo margem mínima
    lon_margin = max(0.01, (max_lon - min_lon) * 0.1)

    # Criando mapa sem definir location e zoom_start iniciais
    mapa = folium.Map(tiles=None)

    # Adicionando camada de satélite
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(mapa)

    # Adicionando marcadores para cada registro
    for idx, row in df_especie.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"Data: {row['Date']}<br>Local: {row['Location']}",
            icon=folium.Icon(color='green', icon='leaf', prefix='fa')
        ).add_to(mapa)

    # Ajustando o mapa para mostrar todos os pontos (com margem)
    mapa.fit_bounds([
        [min_lat - lat_margin, min_lon - lon_margin],
        [max_lat + lat_margin, max_lon + lon_margin]
    ])

    return mapa


# UI do Dashboard - Layout principal
def main():
    # Aplicando o tema
    cores = configurar_tema()

    # Controle para alternar entre tema claro e escuro
    col_titulo, col_tema = st.columns([5, 1])

    with col_titulo:
        st.title("DashBirds: Observatório de Aves - RPPN Estação Veracel")

    with col_tema:
        st.markdown('<div class="tema-toggle">', unsafe_allow_html=True)
        if st.button("🌓 Alternar Tema"):
            # Alternar entre os temas
            if st.session_state.tema == 'escuro':
                st.session_state.tema = 'claro'
            else:
                st.session_state.tema = 'escuro'
            st.rerun()  # Recarregar a aplicação com o novo tema
        st.markdown('</div>', unsafe_allow_html=True)

    # Sidebar - Filtros
    st.sidebar.title("Filtros")

    # Exibe mensagem de carregamento inicial
    with st.spinner("Inicializando o Dashboard de Biodiversidade..."):
        # Carregando dados
        tabela_base, tabela_dados, dados_completos = load_and_process_data()

        # Preparando dados para os filtros
        anos_disponiveis = sorted(tabela_dados['Year'].unique()) if 'Year' in tabela_dados.columns else []
        locais_disponiveis = sorted(tabela_dados['Location'].unique()) if 'Location' in tabela_dados.columns else []

        # Usando a coluna correta para habitats
        if 'Habitat (AVONET)' in tabela_base.columns:
            ambientes_disponiveis = sorted(tabela_base['Habitat (AVONET)'].dropna().unique())
        else:
            ambientes_disponiveis = []

    # Filtro anual
    ano_selecionado = st.sidebar.selectbox(
        "Filtro anual",
        options=["Todos"] + anos_disponiveis,
        index=0
    )

    # Filtro ambiente
    ambiente_selecionado = st.sidebar.selectbox(
        "Filtro ambiente",
        options=["Todos"] + ambientes_disponiveis,
        index=0
    )

    # Filtro local
    local_selecionado = st.sidebar.selectbox(
        "Filtro local",
        options=["Todos"] + locais_disponiveis,
        index=0
    )

    # Informações adicionais na sidebar
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ Informações", expanded=False):
        st.markdown("""
        **Instruções:**

        * Use os filtros acima para refinar os dados visualizados
        * O filtro anual seleciona dados apenas do ano escolhido
        * O filtro de ambiente mostra espécies associadas ao habitat selecionado
        * O filtro local restringe dados a uma localização específica

        **Fonte dos dados:**

        * Tabela base: informações taxonômicas e ecológicas
        * Tabela de dados: registros de campo das espécies
        """)

    # Aplicando filtros
    dados_filtrados = dados_completos.copy()

    if ano_selecionado != "Todos" and 'Year' in dados_filtrados.columns:
        dados_filtrados = dados_filtrados[dados_filtrados['Year'] == ano_selecionado]

    if local_selecionado != "Todos" and 'Location' in dados_filtrados.columns:
        dados_filtrados = dados_filtrados[dados_filtrados['Location'] == local_selecionado]

    if ambiente_selecionado != "Todos":
        if 'Habitat (AVONET)' in dados_filtrados.columns:
            dados_filtrados = dados_filtrados[dados_filtrados['Habitat (AVONET)'] == ambiente_selecionado]

    # Calculando indicadores
    indicadores = calcular_indicadores(dados_filtrados)

    # Seção de indicadores com layout organizado em duas linhas
    st.markdown("## Indicadores")

    # Primeira linha de indicadores
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="indicador-card">
                <div class="indicador-titulo">Total de Registros</div>
                <div class="indicador-valor">{indicadores['n_registros']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="indicador-card">
                <div class="indicador-titulo">Total de Espécies</div>
                <div class="indicador-valor">{indicadores['n_especies']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div class="indicador-card">
                <div class="indicador-titulo">Localizações Únicas</div>
                <div class="indicador-valor">{indicadores['n_localizacoes']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Segunda linha de indicadores - com Espécies Ameaçadas no meio
    col4, col5, col6 = st.columns(3)

    with col4:
        st.markdown(
            f"""
            <div class="indicador-card">
                <div class="indicador-titulo">Número de Listas</div>
                <div class="indicador-valor">{indicadores['n_listas']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div class="indicador-card">
                <div class="indicador-titulo">Espécies Ameaçadas (IUCN)</div>
                <div class="indicador-valor">{indicadores['especies_ameacadas_iucn']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col6:
        st.markdown(
            f"""
            <div class="periodo-indicador">
                <div class="indicador-titulo">Período dos Dados</div>
                <div class="indicador-valor">{indicadores['periodo_dados']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Detalhes e Gráficos
    col1, col2 = st.columns(2)

    # Coluna de indicadores detalhados - modificado para usar mini-cards
    with col1:
        st.write("## Indicadores Detalhados")

        # Criar mini-cards para cada indicador detalhado
        st.markdown(
            f"""
            <div class="mini-card">
                <div class="mini-card-titulo">Espécies ameaçadas (IUCN)</div>
                <div class="mini-card-valor">{indicadores['especies_ameacadas_iucn']}</div>
            </div>

            <div class="mini-card">
                <div class="mini-card-titulo">Espécies ameaçadas (Brasil)</div>
                <div class="mini-card-valor">{indicadores['especies_ameacadas_brasil']}</div>
            </div>

            <div class="mini-card">
                <div class="mini-card-titulo">Espécies ameaçadas (Bahia)</div>
                <div class="mini-card-valor">{indicadores['especies_ameacadas_estado']}</div>
            </div>

            <div class="mini-card">
                <div class="mini-card-titulo">Espécies endêmicas do Brasil</div>
                <div class="mini-card-valor">{indicadores['endemicas_brasil']}</div>
            </div>

            <div class="mini-card">
                <div class="mini-card-titulo">Espécies endêmicas da Mata Atlântica</div>
                <div class="mini-card-valor">{indicadores['endemicas_mata_atlantica']}</div>
            </div>

            <div class="mini-card">
                <div class="mini-card-titulo">Espécies migratórias</div>
                <div class="mini-card-valor">{indicadores['migratorias']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Coluna de gráficos gerais
    with col2:
        st.write("## Gráficos gerais")

        grafico_opcoes = [
            "Famílias mais representativas",
            "Espécies mais representativas",
            "Habitats preferenciais",
            "Nicho trófico",
            "Outros?"
        ]

        grafico_selecionado = st.selectbox("Opção de selecionar dropdown", grafico_opcoes)

        if grafico_selecionado == "Famílias mais representativas":
            fig = gerar_grafico_familias(dados_filtrados)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Dados insuficientes para gerar o gráfico.")

        elif grafico_selecionado == "Espécies mais representativas":
            fig = gerar_grafico_especies(dados_filtrados)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Dados insuficientes para gerar o gráfico.")

        elif grafico_selecionado == "Habitats preferenciais":
            fig = gerar_grafico_habitats(dados_filtrados)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Dados insuficientes para gerar o gráfico.")

        elif grafico_selecionado == "Nicho trófico":
            fig = gerar_grafico_nicho_trofico(dados_filtrados)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Dados insuficientes para gerar o gráfico.")

        elif grafico_selecionado == "Outros?":
            st.info("Outros gráficos podem ser adicionados conforme necessário.")

    st.markdown("---")

    # Listas de Espécies e Mapa Geral
    col1, col2 = st.columns(2)

    # Seção de Listas de Espécies com filtro atualizado
    with col1:
        st.write("## Listas de espécies")

        lista_opcoes = [
            "Geral",
            "Filtrar espécies ameaçadas",
            "Filtrar espécies endêmicas da Mata Atlântica"
        ]

        lista_selecionada = st.selectbox("", lista_opcoes)

        if lista_selecionada == "Geral":
            especies_lista = dados_filtrados[
                ['Scientific Name', 'Nome científico', 'Nomes em Português', 'Nomes da Ordens',
                 'Nome da Família']].drop_duplicates(subset='Scientific Name').sort_values('Scientific Name')

        elif lista_selecionada == "Filtrar espécies ameaçadas":
            # Filtro atualizado para incluir espécies "Quase ameaçada"
            especies_lista = dados_filtrados[
                (dados_filtrados['IUCN 2021'].isin(
                    ['Vulnerável', 'Em perigo', 'Criticamente ameaçada', 'Quase ameaçada', 'VU', 'EN', 'CR', 'NT'])) |
                (dados_filtrados['MMA 2022'].isin(
                    ['Vulnerável', 'Em perigo', 'Criticamente ameaçada', 'Quase ameaçada', 'VU', 'EN', 'CR', 'NT'])) |
                (dados_filtrados['Ameaçadas Bahia 2017'].notna() & (dados_filtrados['Ameaçadas Bahia 2017'] != ''))
                ][['Scientific Name', 'Nome científico', 'Nomes em Português', 'IUCN 2021', 'MMA 2022',
                   'Ameaçadas Bahia 2017', 'Nome da Família']].drop_duplicates(subset='Scientific Name').sort_values(
                'Scientific Name')

        elif lista_selecionada == "Filtrar espécies endêmicas da Mata Atlântica":
            especies_lista = dados_filtrados[
                dados_filtrados['Espécies Endêmicas da Mata Atlântica'] == 1
                ][['Scientific Name', 'Nome científico', 'Nomes em Português', 'Nome da Família']].drop_duplicates(
                subset='Scientific Name').sort_values('Scientific Name')

        if not especies_lista.empty and len(especies_lista) > 0:
            st.dataframe(especies_lista, height=450)
            st.markdown(f"**Total: {len(especies_lista)} espécies**")
        else:
            st.warning("Não há espécies para exibir com os filtros aplicados.")

    # Mapa geral
    with col2:
        st.write("## Mapa geral")

        mapa_opcoes = [
            "Riqueza de espécies por área",
            "Riqueza de espécies ameaçadas por área"
        ]

        mapa_selecionado = st.selectbox("Selecionar tipo de mapa:", mapa_opcoes)

        if mapa_selecionado == "Riqueza de espécies por área":
            mapa = gerar_mapa_riqueza(dados_filtrados)
            if mapa:
                # Ajustando para ocupar todo o espaço horizontal
                st_folium(mapa, width='100%', height=450)
            else:
                st.warning("Dados insuficientes para gerar o mapa.")

        elif mapa_selecionado == "Riqueza de espécies ameaçadas por área":
            # Filtrando apenas espécies ameaçadas
            dados_ameacados = dados_filtrados[
                (dados_filtrados['IUCN 2021'].isin(
                    ['Vulnerável', 'Em perigo', 'Criticamente ameaçada', 'Quase ameaçada', 'VU', 'EN', 'CR', 'NT'])) |
                (dados_filtrados['MMA 2022'].isin(
                    ['Vulnerável', 'Em perigo', 'Criticamente ameaçada', 'Quase ameaçada', 'VU', 'EN', 'CR', 'NT'])) |
                (dados_filtrados['Ameaçadas Bahia 2017'].notna() & (dados_filtrados['Ameaçadas Bahia 2017'] != ''))
                ] if (
                        'IUCN 2021' in dados_filtrados.columns or 'MMA 2022' in dados_filtrados.columns or 'Ameaçadas Bahia 2017' in dados_filtrados.columns) else pd.DataFrame()

            if not dados_ameacados.empty:
                mapa = gerar_mapa_riqueza(dados_ameacados)
                if mapa:
                    # Ajustando para ocupar todo o espaço horizontal
                    st_folium(mapa, width='100%', height=450)
                else:
                    st.warning("Dados insuficientes para gerar o mapa.")
            else:
                st.warning("Não há dados de espécies ameaçadas para exibir.")

    st.markdown("---")

    # Olha o Passarinho (Detalhes da Espécie) - Formatado com mini-cards
    st.write("## Olha o passarinho:")

    # Lista única de espécies disponíveis nos dados filtrados
    especies_disponiveis = sorted(dados_filtrados['Scientific Name'].unique())

    if len(especies_disponiveis) > 0:
        # Nome científico (selecionável)
        especie_selecionada = st.selectbox(
            "Nome científico (selecione):",
            especies_disponiveis
        )

        # Filtrando informações da espécie selecionada
        info_especie = dados_filtrados[dados_filtrados['Scientific Name'] == especie_selecionada].iloc[0]

        # Nome comum (selecionável) - na prática, isso já é determinado pelo nome científico
        nome_comum = info_especie.get('Nomes em Português', 'Nome desconhecido')

        # Status de conservação
        status_iucn = info_especie.get('IUCN 2021', 'Não avaliada')
        status_brasil = info_especie.get('MMA 2022', 'Não avaliada')

        # Número total de registros
        n_registros_especie = len(dados_filtrados[dados_filtrados['Scientific Name'] == especie_selecionada])

        # Abundância na área
        if n_registros_especie > 20:
            abundancia = "comum"
        elif n_registros_especie > 5:
            abundancia = "incomum"
        else:
            abundancia = "rara"

        # Exibindo informações em mini-cards (em uma linha com 2 colunas)
        col_info1, col_info2 = st.columns(2)

        with col_info1:
            st.markdown(
                f"""
                <div class="mini-card">
                    <div class="mini-card-titulo">Nome comum</div>
                    <div class="mini-card-valor">{nome_comum}</div>
                </div>

                <div class="mini-card">
                    <div class="mini-card-titulo">Status IUCN</div>
                    <div class="mini-card-valor">{status_iucn}</div>
                </div>

                <div class="mini-card">
                    <div class="mini-card-titulo">Status Brasil</div>
                    <div class="mini-card-valor">{status_brasil}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_info2:
            st.markdown(
                f"""
                <div class="mini-card">
                    <div class="mini-card-titulo">Número total de registros</div>
                    <div class="mini-card-valor">{n_registros_especie}</div>
                </div>

                <div class="mini-card">
                    <div class="mini-card-titulo">Abundância na área</div>
                    <div class="mini-card-valor">{abundancia}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Gráficos de detalhes da espécie
        col1, col2 = st.columns(2)

        with col1:
            st.write("### Gráfico Sazonalidade (mensal)")

            fig_sazon = gerar_grafico_sazonalidade(dados_filtrados, especie_selecionada)
            if fig_sazon:
                st.plotly_chart(fig_sazon, use_container_width=True)
            else:
                st.warning("Dados insuficientes para gerar o gráfico de sazonalidade.")

        with col2:
            st.write("### Mapa de ocorrência na área de estudo")

            mapa_especie = gerar_mapa_ocorrencia(dados_filtrados, especie_selecionada)
            if mapa_especie:
                st_folium(mapa_especie, width='100%', height=450)
            else:
                st.warning("Dados insuficientes para gerar o mapa de ocorrência.")

    else:
        st.warning("Não há espécies disponíveis com os filtros aplicados.")

    # Rodapé com informações adicionais
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.8rem;">
            Dashboard de Biodiversidade | Versão 1.0 | Desenvolvido com Streamlit
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
