import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Configuração da página
st.set_page_config(
    page_title="Pipefy Process Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Caminho para o arquivo Excel (relativo ao script)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'maze_process-intelligence.xlsx')

# Cache de dados
@st.cache_data
def load_data():
    """Carrega e processa os dados do Excel"""
    xls = pd.ExcelFile(EXCEL_PATH)

    data = {
        'tempo_uso': pd.read_excel(xls, 'tempo de uso de Pipefy'),
        'frequencia': pd.read_excel(xls, 'frequência'),
        'departamento': pd.read_excel(xls, 'departamento'),
        'objetivo_freq': pd.read_excel(xls, 'objetivo da área x frequência'),
        'facilidade_tempo': pd.read_excel(xls, 'facilidade x tempo'),
        'utilidade_tempo': pd.read_excel(xls, 'utilidade + tempo'),
        'comentarios_facilidade': pd.read_excel(xls, 'comentários facilidade'),
        'comentarios_utilidade': pd.read_excel(xls, 'comentários utilidade')
    }

    return data

@st.cache_data
def calculate_metrics(data):
    """Calcula métricas principais"""
    metrics = {}

    # Total de respondentes
    metrics['total_respondentes'] = len(data['tempo_uso'])

    # Frequência de análises
    freq_counts = data['frequencia']['Frequência de análises'].value_counts()
    freq_alta = freq_counts.get('Diariamente', 0) + freq_counts.get('Semanalmente', 0)
    total_freq = len(data['frequencia'])
    metrics['taxa_engajamento'] = round((freq_alta / total_freq * 100), 1) if total_freq > 0 else 0

    # Facilidade de uso
    facil_counts = data['facilidade_tempo']['Facilidade de uso'].value_counts()
    facilidade_positiva = facil_counts.get('Muito fácil', 0) + facil_counts.get('Fácil', 0)
    total_facilidade = len(data['facilidade_tempo'])
    metrics['taxa_facilidade'] = round((facilidade_positiva / total_facilidade * 100), 1) if total_facilidade > 0 else 0

    # Utilidade geral
    util_geral_counts = data['utilidade_tempo']['Utilidade'].value_counts()
    utilidade_positiva = util_geral_counts.get('Muito útil', 0) + util_geral_counts.get('Útil', 0)
    total_utilidade = len(data['utilidade_tempo'])
    metrics['taxa_utilidade'] = round((utilidade_positiva / total_utilidade * 100), 1) if total_utilidade > 0 else 0

    return metrics

def create_donut_chart(df, column, title, order=None):
    """Cria gráfico de rosca (donut)"""
    counts = df[column].value_counts()

    if order:
        counts = counts.reindex(order, fill_value=0)

    fig = go.Figure(data=[go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.4,
        marker=dict(colors=px.colors.qualitative.Set2)
    )])

    fig.update_layout(
        title=title,
        height=400,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5)
    )

    return fig

def create_bar_chart(df, column, title, orientation='h'):
    """Cria gráfico de barras"""
    counts = df[column].value_counts().head(10)

    if orientation == 'h':
        fig = go.Figure(data=[go.Bar(
            x=counts.values,
            y=counts.index,
            orientation='h',
            marker=dict(color='#4F46E5')
        )])
        fig.update_layout(height=400, xaxis_title="Quantidade", yaxis_title="")
    else:
        fig = go.Figure(data=[go.Bar(
            x=counts.index,
            y=counts.values,
            marker=dict(color='#4F46E5')
        )])
        fig.update_layout(height=400, xaxis_title="", yaxis_title="Quantidade")

    fig.update_layout(title=title, showlegend=False)
    return fig

# Carregar dados
data = load_data()
metrics = calculate_metrics(data)

# Header
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    </style>
    <div class="main-header">
        <h1>📊 Pipefy Process Intelligence</h1>
        <p>Dashboard de Análise de Dados</p>
    </div>
""", unsafe_allow_html=True)

# KPIs principais
st.markdown("### 📈 Métricas Principais")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="👥 Total de Respondentes",
        value=metrics['total_respondentes'],
        help="Total de participantes da pesquisa"
    )

with col2:
    st.metric(
        label="✅ Taxa de Utilidade",
        value=f"{metrics['taxa_utilidade']}%",
        delta=f"{metrics['taxa_utilidade'] - 50:.1f}% acima da média",
        help="Percentual de usuários que consideram útil ou muito útil"
    )

with col3:
    st.metric(
        label="⚡ Engajamento Alto",
        value=f"{metrics['taxa_engajamento']}%",
        delta=f"{metrics['taxa_engajamento'] - 50:.1f}% acima da média",
        help="Percentual de usuários que fazem análises diária ou semanalmente"
    )

with col4:
    st.metric(
        label="😊 Facilidade de Uso",
        value=f"{metrics['taxa_facilidade']}%",
        delta=f"{metrics['taxa_facilidade'] - 50:.1f}% acima da média",
        help="Percentual de usuários que acham fácil ou muito fácil"
    )

st.markdown("---")

# Sidebar com filtros
with st.sidebar:
    st.markdown("## 🔍 Filtros")

    st.markdown("### Informações")
    st.info(f"""
    **Total de respostas:**
    - Tempo de uso: {len(data['tempo_uso'])}
    - Frequência: {len(data['frequencia'])}
    - Facilidade: {len(data['facilidade_tempo'])}
    - Utilidade: {len(data['utilidade_tempo'])}
    """)

    st.markdown("### 📥 Exportar Dados")

    # Botões de download
    csv_tempo = data['tempo_uso'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Tempo de Uso (CSV)",
        data=csv_tempo,
        file_name="tempo_uso.csv",
        mime="text/csv"
    )

    csv_freq = data['frequencia'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Frequência (CSV)",
        data=csv_freq,
        file_name="frequencia.csv",
        mime="text/csv"
    )

# Gráficos principais
st.markdown("### 📊 Visualizações")

# Primeira linha de gráficos
col1, col2 = st.columns(2)

with col1:
    ordem_tempo = ['Menos de 1 mês', 'Entre 1 e 6 meses', 'Entre 6 meses e 1 ano', 'Mais de 1 ano']
    fig1 = create_donut_chart(data['tempo_uso'], 'Tempo de Pipefy', 'Tempo de Uso do Pipefy', ordem_tempo)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = create_donut_chart(data['frequencia'], 'Frequência de análises', 'Frequência de Análises')
    st.plotly_chart(fig2, use_container_width=True)

# Segunda linha de gráficos
col3, col4 = st.columns(2)

with col3:
    ordem_facil = ['Muito fácil', 'Fácil', 'Neutro', 'Difícil', 'Muito difícil']
    fig3 = create_donut_chart(data['facilidade_tempo'], 'Facilidade de uso', 'Facilidade de Uso', ordem_facil)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    ordem_util = ['Muito útil', 'Útil', 'Neutro', 'Pouco útil', 'Nada útil']
    fig4 = create_donut_chart(data['utilidade_tempo'], 'Utilidade', 'Utilidade Geral', ordem_util)
    st.plotly_chart(fig4, use_container_width=True)

# Terceira linha - Gráficos de barra
st.markdown("---")

col5, col6 = st.columns(2)

with col5:
    fig5 = create_bar_chart(data['departamento'], 'Departamento', 'Top 10 Departamentos')
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    fig6 = create_bar_chart(data['objetivo_freq'], 'Objetivo da área', 'Objetivos da Área')
    st.plotly_chart(fig6, use_container_width=True)

# Comentários
st.markdown("---")
st.markdown("### 💬 Feedback dos Usuários")

tab1, tab2 = st.tabs(["💭 Comentários sobre Facilidade", "✨ Comentários sobre Utilidade"])

with tab1:
    st.markdown(f"**{len(data['comentarios_facilidade'])} comentários no total**")

    comentarios_facil = data['comentarios_facilidade']['Answer'].dropna()

    for i, comentario in enumerate(comentarios_facil.head(10), 1):
        with st.expander(f"Comentário #{i}", expanded=(i <= 3)):
            st.write(f'"{comentario}"')

with tab2:
    st.markdown(f"**{len(data['comentarios_utilidade'])} comentários no total**")

    comentarios_util = data['comentarios_utilidade']['Answer'].dropna()

    for i, comentario in enumerate(comentarios_util.head(10), 1):
        with st.expander(f"Comentário #{i}", expanded=(i <= 3)):
            st.write(f'"{comentario}"')

# Análise detalhada (expandível)
st.markdown("---")
with st.expander("📋 Ver Dados Detalhados"):
    st.markdown("### Distribuições Completas")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Tempo de Uso**")
        tempo_dist = data['tempo_uso']['Tempo de Pipefy'].value_counts()
        tempo_df = pd.DataFrame({
            'Categoria': tempo_dist.index,
            'Quantidade': tempo_dist.values,
            'Percentual': (tempo_dist.values / len(data['tempo_uso']) * 100).round(1)
        })
        st.dataframe(tempo_df, use_container_width=True)

        st.markdown("**Facilidade de Uso**")
        facil_dist = data['facilidade_tempo']['Facilidade de uso'].value_counts()
        facil_df = pd.DataFrame({
            'Categoria': facil_dist.index,
            'Quantidade': facil_dist.values,
            'Percentual': (facil_dist.values / len(data['facilidade_tempo']) * 100).round(1)
        })
        st.dataframe(facil_df, use_container_width=True)

    with col2:
        st.markdown("**Frequência de Análises**")
        freq_dist = data['frequencia']['Frequência de análises'].value_counts()
        freq_df = pd.DataFrame({
            'Categoria': freq_dist.index,
            'Quantidade': freq_dist.values,
            'Percentual': (freq_dist.values / len(data['frequencia']) * 100).round(1)
        })
        st.dataframe(freq_df, use_container_width=True)

        st.markdown("**Utilidade**")
        util_dist = data['utilidade_tempo']['Utilidade'].value_counts()
        util_df = pd.DataFrame({
            'Categoria': util_dist.index,
            'Quantidade': util_dist.values,
            'Percentual': (util_dist.values / len(data['utilidade_tempo']) * 100).round(1)
        })
        st.dataframe(util_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Dashboard de Process Intelligence - Dados da pesquisa Pipefy</p>
        <p style='font-size: 0.8rem;'>Desenvolvido com Streamlit 🎈</p>
    </div>
""", unsafe_allow_html=True)
