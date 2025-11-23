import os
import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

# -----------------------------
# CONFIGURAÇÃO DO APLICATIVO
# -----------------------------
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# -----------------------------
# BANCO DE DADOS
# -----------------------------
def db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()

    # Tabela Protocolos
    conn.execute("""
        CREATE TABLE IF NOT EXISTS protocolos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            solicitante TEXT,
            endereco TEXT,
            tipo_servico TEXT,
            descricao TEXT,
            status TEXT
        )
    """)

    # Tabela Projetos
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            descricao TEXT,
            responsavel TEXT,
            status TEXT,
            inicio TEXT,
            fim TEXT
        )
    """)

    conn.commit()


# Inicializa o banco ao iniciar
init_db()


# -----------------------------
# ROTA PRINCIPAL
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')


# -----------------------------
# PROTOCOLOS
# -----------------------------
@app.route('/protocolos')
def protocolos():
    conn = db()
    protocolos = conn.execute('SELECT * FROM protocolos ORDER BY id DESC').fetchall()
    return render_template('protocolos.html', protocolos=protocolos)


@app.route('/protocolo/novo', methods=['GET', 'POST'])
def protocolo_novo():

    if request.method == 'POST':
        conn = db()
        conn.execute("""
            INSERT INTO protocolos (data, solicitante, endereco, tipo_servico, descricao, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(datetime.datetime.now()),
            request.form['solicitante'],
            request.form['endereco'],
            request.form['tipo_servico'],
            request.form['descricao'],
            "Aberto"
        ))
        conn.commit()

        return redirect(url_for('protocolos'))

    return render_template('protocolo_form.html')


# -----------------------------
# PROJETOS
# -----------------------------
@app.route('/projetos')
def projetos():
    conn = db()
    projetos = conn.execute('SELECT * FROM projetos ORDER BY id DESC').fetchall()
    return render_template('projetos.html', projetos=projetos)


@app.route('/projeto/novo', methods=['GET', 'POST'])
def projeto_novo():

    if request.method == 'POST':
        conn = db()
        conn.execute("""
            INSERT INTO projetos (nome, descricao, responsavel, status, inicio, fim)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form['nome'],
            request.form['descricao'],
            request.form['responsavel'],
            request.form['status'],
            request.form['inicio'],
            request.form['fim']
        ))
        conn.commit()

        return redirect(url_for('projetos'))

    return render_template('projeto_form.html')


# -----------------------------
# UPLOAD DE ARQUIVOS
# -----------------------------
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['arquivo']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return "OK"


# -----------------------------
# EXECUÇÃO LOCAL
# -----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
