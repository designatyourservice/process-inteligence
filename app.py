from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Caminho para o arquivo Excel
EXCEL_PATH = '/Users/thomazkrause/Server/process-inteligence/maze_process-intelligence.xlsx'

def load_data():
    """Carrega e processa os dados do Excel"""
    xls = pd.ExcelFile(EXCEL_PATH)

    # Carregar todas as planilhas relevantes
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

def calculate_metrics(data):
    """Calcula métricas principais"""
    metrics = {}

    # Total de respondentes
    metrics['total_respondentes'] = len(data['tempo_uso'])

    # Tempo de uso
    tempo_counts = data['tempo_uso']['Tempo de Pipefy'].value_counts()
    metrics['tempo_uso'] = tempo_counts.to_dict()

    # Frequência de análises
    freq_counts = data['frequencia']['Frequência de análises'].value_counts()
    metrics['frequencia'] = freq_counts.to_dict()

    # Departamentos top 10
    dept_counts = data['departamento']['Departamento'].value_counts().head(10)
    metrics['departamentos'] = dept_counts.to_dict()

    # Utilidade da área
    util_counts = data['departamento']['Utilidade da área'].value_counts()
    metrics['utilidade_area'] = util_counts.to_dict()

    # Objetivos
    obj_counts = data['objetivo_freq']['Objetivo da área'].value_counts()
    metrics['objetivos'] = obj_counts.to_dict()

    # Facilidade de uso
    facil_counts = data['facilidade_tempo']['Facilidade de uso'].value_counts()
    metrics['facilidade'] = facil_counts.to_dict()

    # Utilidade geral
    util_geral_counts = data['utilidade_tempo']['Utilidade'].value_counts()
    metrics['utilidade_geral'] = util_geral_counts.to_dict()

    # Taxa de satisfação
    facilidade_positiva = facil_counts.get('Muito fácil', 0) + facil_counts.get('Fácil', 0)
    total_facilidade = len(data['facilidade_tempo'])
    metrics['taxa_facilidade'] = round((facilidade_positiva / total_facilidade * 100), 1) if total_facilidade > 0 else 0

    utilidade_positiva = util_geral_counts.get('Muito útil', 0) + util_geral_counts.get('Útil', 0)
    total_utilidade = len(data['utilidade_tempo'])
    metrics['taxa_utilidade'] = round((utilidade_positiva / total_utilidade * 100), 1) if total_utilidade > 0 else 0

    # Engajamento
    freq_alta = freq_counts.get('Diariamente', 0) + freq_counts.get('Semanalmente', 0)
    total_freq = len(data['frequencia'])
    metrics['taxa_engajamento'] = round((freq_alta / total_freq * 100), 1) if total_freq > 0 else 0

    # Comentários
    metrics['total_comentarios_facilidade'] = len(data['comentarios_facilidade'])
    metrics['total_comentarios_utilidade'] = len(data['comentarios_utilidade'])

    return metrics

@app.route('/')
def index():
    """Página principal do dashboard"""
    data = load_data()
    metrics = calculate_metrics(data)

    # Comentários recentes
    comentarios_facilidade = data['comentarios_facilidade']['Answer'].dropna().head(5).tolist()
    comentarios_utilidade = data['comentarios_utilidade']['Answer'].head(5).tolist()

    return render_template('index.html',
                         metrics=metrics,
                         comentarios_facilidade=comentarios_facilidade,
                         comentarios_utilidade=comentarios_utilidade)

@app.route('/api/tempo-uso')
def api_tempo_uso():
    """API endpoint para dados de tempo de uso"""
    data = load_data()
    tempo_counts = data['tempo_uso']['Tempo de Pipefy'].value_counts()

    # Ordenar de forma lógica
    ordem = ['Menos de 1 mês', 'Entre 1 e 6 meses', 'Entre 6 meses e 1 ano', 'Mais de 1 ano']
    resultado = []
    for label in ordem:
        if label in tempo_counts.index:
            resultado.append({'label': label, 'value': int(tempo_counts[label])})

    return jsonify(resultado)

@app.route('/api/frequencia')
def api_frequencia():
    """API endpoint para dados de frequência"""
    data = load_data()
    freq_counts = data['frequencia']['Frequência de análises'].value_counts()

    resultado = [{'label': k, 'value': int(v)} for k, v in freq_counts.items()]
    return jsonify(resultado)

@app.route('/api/departamentos')
def api_departamentos():
    """API endpoint para dados de departamentos"""
    data = load_data()
    dept_counts = data['departamento']['Departamento'].value_counts().head(10)

    resultado = [{'label': k, 'value': int(v)} for k, v in dept_counts.items()]
    return jsonify(resultado)

@app.route('/api/facilidade')
def api_facilidade():
    """API endpoint para facilidade de uso"""
    data = load_data()
    facil_counts = data['facilidade_tempo']['Facilidade de uso'].value_counts()

    # Ordenar de forma lógica
    ordem = ['Muito fácil', 'Fácil', 'Neutro', 'Difícil', 'Muito difícil']
    resultado = []
    for label in ordem:
        if label in facil_counts.index:
            resultado.append({'label': label, 'value': int(facil_counts[label])})

    return jsonify(resultado)

@app.route('/api/utilidade')
def api_utilidade():
    """API endpoint para utilidade geral"""
    data = load_data()
    util_counts = data['utilidade_tempo']['Utilidade'].value_counts()

    # Ordenar de forma lógica
    ordem = ['Muito útil', 'Útil', 'Neutro', 'Pouco útil', 'Nada útil']
    resultado = []
    for label in ordem:
        if label in util_counts.index:
            resultado.append({'label': label, 'value': int(util_counts[label])})

    return jsonify(resultado)

@app.route('/api/objetivos')
def api_objetivos():
    """API endpoint para objetivos da área"""
    data = load_data()
    obj_counts = data['objetivo_freq']['Objetivo da área'].value_counts()

    resultado = [{'label': k, 'value': int(v)} for k, v in obj_counts.items()]
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
