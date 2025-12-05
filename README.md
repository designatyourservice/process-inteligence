# Dashboard Pipefy Process Intelligence

Dashboard interativo para visualização de dados de pesquisa sobre Process Intelligence do Pipefy.

## Características

- 📊 Gráficos interativos com Plotly
- 📱 Design responsivo e moderno
- 🎨 Interface intuitiva com Streamlit
- ⚡ Atualização em tempo real
- 💬 Visualização de comentários dos usuários
- 📥 Exportação de dados em CSV
- 🔍 Filtros e análises detalhadas

## Instalação

1. Navegue até o diretório do projeto:
```bash
cd /Users/thomazkrause/Server/process-inteligence/pipefy-dashboard
```

2. Instale as dependências:
```bash
pip3 install -r requirements.txt
```

## Executar a aplicação

```bash
streamlit run streamlit_app.py
```

O dashboard estará disponível em: http://localhost:8501

## Estrutura do Projeto

```
pipefy-dashboard/
├── streamlit_app.py        # Aplicação Streamlit principal
├── requirements.txt        # Dependências Python
├── .streamlit/
│   └── config.toml        # Configurações e tema
└── README.md              # Documentação
```

## Funcionalidades

### 📈 KPIs Principais
- Total de respondentes
- Taxa de utilidade (% de usuários satisfeitos)
- Taxa de engajamento (% de uso frequente)
- Taxa de facilidade de uso

### 📊 Visualizações Interativas
- Tempo de uso do Pipefy (gráfico de rosca)
- Frequência de análises (gráfico de rosca)
- Facilidade de uso (gráfico de rosca)
- Utilidade geral (gráfico de rosca)
- Top 10 departamentos (gráfico de barras)
- Objetivos da área (gráfico de barras)

### 💬 Feedback Qualitativo
- Comentários sobre facilidade de uso
- Comentários sobre utilidade
- Seções expansíveis para navegação fácil

### 📥 Exportação de Dados
- Exportar dados de tempo de uso em CSV
- Exportar dados de frequência em CSV
- Tabelas detalhadas com percentuais

## Métricas Disponíveis

- Total de respondentes: 247
- Distribuição por tempo de uso
- Frequência de análises
- Distribuição por departamento (37 únicos)
- Facilidade de uso
- Utilidade geral
- Objetivos da área
- 49 comentários sobre facilidade
- 19 comentários sobre utilidade

## Tecnologias Utilizadas

- **Framework**: Streamlit
- **Visualização**: Plotly
- **Processamento de Dados**: Pandas
- **Leitura de Excel**: OpenPyXL
- **Linguagem**: Python 3.9+

## Deploy

### Streamlit Cloud (Gratuito)

1. Faça push do código para GitHub
2. Acesse https://streamlit.io/cloud
3. Conecte seu repositório
4. Configure o arquivo principal como `streamlit_app.py`
5. Deploy automático!

### Local

```bash
streamlit run streamlit_app.py --server.port 8501
```

## Customização

Edite `.streamlit/config.toml` para personalizar:
- Cores do tema
- Porta do servidor
- Configurações de cache
- E mais...

## Sobre

Dashboard desenvolvido para análise de dados de pesquisa sobre Process Intelligence do Pipefy, permitindo visualização interativa de métricas de uso, satisfação e feedback dos usuários.
