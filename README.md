# Dashboard Pipefy Process Intelligence

Dashboard interativo para visualização de dados de pesquisa sobre Process Intelligence do Pipefy.

## Características

- 📊 Gráficos interativos com Chart.js
- 📱 Design responsivo
- 🎨 Interface moderna e intuitiva
- ⚡ API REST para dados em tempo real
- 💬 Visualização de comentários dos usuários

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
python3 app.py
```

O dashboard estará disponível em: http://localhost:5000

## Estrutura do Projeto

```
pipefy-dashboard/
├── app.py                  # Aplicação Flask principal
├── requirements.txt        # Dependências Python
├── templates/
│   └── index.html         # Template HTML do dashboard
└── static/
    └── css/
        └── style.css      # Estilos CSS
```

## Endpoints da API

- `GET /` - Dashboard principal
- `GET /api/tempo-uso` - Dados de tempo de uso
- `GET /api/frequencia` - Dados de frequência de análises
- `GET /api/departamentos` - Dados de departamentos
- `GET /api/facilidade` - Dados de facilidade de uso
- `GET /api/utilidade` - Dados de utilidade geral
- `GET /api/objetivos` - Dados de objetivos da área

## Métricas Disponíveis

- Total de respondentes
- Taxa de utilidade
- Taxa de engajamento
- Taxa de facilidade de uso
- Distribuição por tempo de uso
- Frequência de análises
- Distribuição por departamento
- Objetivos da área
- Comentários dos usuários

## Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualização**: Chart.js
- **Processamento de Dados**: Pandas
