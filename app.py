#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portal Cotando - Sistema de Cotação de Preços
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'portal-cotando-segredo-super-forte-2026')

# Configuração do banco
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portal_cotando.db')

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Faça login para acessar o painel administrativo.'

# ==================== PRODUTOS FIXOS ====================
PRODUTOS = [
    {"id": 1, "descricao": "Aipim Tolete Pacote IQF 1kg Congelado Fardo 10kg", "embalagem": "FD 10KG", "qtd": 1, "unidade": "FD"},
    {"id": 2, "descricao": "Almôndega Mista 25g Pacote 1kg Congelada", "embalagem": "CX 4KG", "qtd": 1, "unidade": "CX"},
    {"id": 3, "descricao": "Coxinha da Asa de Frango Congelada Pacote IQF 1kg", "embalagem": "CX 15KG", "qtd": 1, "unidade": "CX"},
    {"id": 4, "descricao": "Fígado de Frango Congelado Bandeja 500g", "embalagem": "CX 24UN", "qtd": 1, "unidade": "CX"},
    {"id": 5, "descricao": "Filé de Coxa com Sobrecoxa de Frango Sem Osso e com Pele Congelado Pacote IQF 1kg", "embalagem": "CX 15KG", "qtd": 1, "unidade": "CX"},
    {"id": 6, "descricao": "Filé de Meio Peito de Frango Sem Osso e Sem Pele (Bife) Congelado Pacote IQF 1kg", "embalagem": "CX 10KG", "qtd": 1, "unidade": "CX"},
    {"id": 7, "descricao": "Filé de Tilápia V Sem Espinha Congelada Pacote 800g", "embalagem": "CX 12UN", "qtd": 2, "unidade": "CX"},
    {"id": 8, "descricao": "Filezinho Sassami de Frango Congelado Pacote IQF 1kg", "embalagem": "CX 10KG", "qtd": 1, "unidade": "CX"},
    {"id": 9, "descricao": "Frango a Passarinho Congelado Pacote IQF 1kg", "embalagem": "CX 10KG", "qtd": 3, "unidade": "CX"},
    {"id": 10, "descricao": "Lasanha Bolonhesa Congelada 1kg", "embalagem": "CX 4UN", "qtd": 1, "unidade": "CX"},
    {"id": 11, "descricao": "Lasanha de Calabresa Congelada 600g", "embalagem": "PCT 3UN", "qtd": 1, "unidade": "PCT"},
    {"id": 12, "descricao": "Linguiça de Frango Pacote de 1kg Congelada", "embalagem": "CX 12KG", "qtd": 2, "unidade": "CX"},
    {"id": 13, "descricao": "Margarina com Sal 500g", "embalagem": "CX 12UN", "qtd": 4, "unidade": "CX"},
    {"id": 14, "descricao": "Margarina sem Sal 500g", "embalagem": "CX 12UN", "qtd": 1, "unidade": "CX"},
    {"id": 15, "descricao": "Meio da Asa de Frango Congelada Pacote IQF 1kg", "embalagem": "CX 10KG", "qtd": 2, "unidade": "CX"},
    {"id": 16, "descricao": "Moela de Frango Congelada Pacote 1kg", "embalagem": "CX 20KG", "qtd": 2, "unidade": "CX"},
    {"id": 17, "descricao": "Nata 45% de Gordura Pote 250g", "embalagem": "CX 12UN", "qtd": 1, "unidade": "CX"},
    {"id": 18, "descricao": "Pés de Galinha Congelado Pacote 1,2kg", "embalagem": "CX 14,4KG", "qtd": 1, "unidade": "CX"},
    {"id": 19, "descricao": "Presunto Fatiado Pacote 200g", "embalagem": "PCT 4UN", "qtd": 3, "unidade": "PCT"},
    {"id": 20, "descricao": "Salsicha Congelada Pacote 5kg", "embalagem": "CX 20KG", "qtd": 3, "unidade": "CX"},
    {"id": 21, "descricao": "Salsicha Hot Dog Resfriada Pacote 500g", "embalagem": "CX 12UN", "qtd": 1, "unidade": "CX"},
    {"id": 22, "descricao": "Sanduíche X-Burger 145g", "embalagem": "PCT 3UN", "qtd": 1, "unidade": "PCT"},
    {"id": 23, "descricao": "Sanduíche X-Burguer Maionese 145g", "embalagem": "PCT 3UN", "qtd": 1, "unidade": "PCT"},
    {"id": 24, "descricao": "Sanduíche X-Burguer Toscana 145g", "embalagem": "PCT 3UN", "qtd": 1, "unidade": "PCT"},
    {"id": 25, "descricao": "Steak de Frango Empanado 100g", "embalagem": "CX 60UN", "qtd": 1, "unidade": "CX"},
]

CONDICOES_PAGAMENTO = [
    "À vista",
    "7 dias",
    "14 dias",
    "21 dias",
    "28 dias",
    "30 dias",
    "42 dias",
    "45 dias",
    "60 dias",
    "90 dias",
    "7 + 14 + 21",
    "14 + 21 + 28",
    "15 + 30 + 45",
    "20 + 40 + 60",
    "21 + 28 + 35",
    "28 + 35 + 42",
    "30 + 60",
    "30 + 60 + 90",
    "45 + 90",
]

# ==================== BANCO DE DADOS ====================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Tabela de administradores
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Tabela de fornecedores
    c.execute('''
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            razao_social TEXT NOT NULL,
            cnpj TEXT,
            contato TEXT,
            telefone TEXT,
            email TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de cotações (cabeçalho)
    c.execute('''
        CREATE TABLE IF NOT EXISTS cotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor_id INTEGER NOT NULL,
            responsavel TEXT NOT NULL,
            prazo_entrega TEXT NOT NULL,
            condicao_pagamento TEXT NOT NULL,
            observacoes TEXT,
            total_geral REAL DEFAULT 0,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
        )
    ''')

    # Tabela de itens da cotação
    c.execute('''
        CREATE TABLE IF NOT EXISTS cotacao_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cotacao_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            embalagem TEXT,
            quantidade REAL NOT NULL,
            unidade TEXT,
            preco_unitario REAL NOT NULL,
            preco_total REAL NOT NULL,
            FOREIGN KEY (cotacao_id) REFERENCES cotacoes (id)
        )
    ''')

    # Criar admin padrão se não existir
    c.execute('SELECT id FROM admins WHERE username = ?', ('admin',))
    if not c.fetchone():
        password_hash = generate_password_hash('M@nu122810')
        c.execute('INSERT INTO admins (username, password_hash) VALUES (?, ?)', ('admin', password_hash))

    conn.commit()
    conn.close()

# ==================== MODELOS / LOGIN ====================

class Admin(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    admin = conn.execute('SELECT * FROM admins WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if admin:
        return Admin(admin['id'], admin['username'])
    return None

# ==================== ROTAS PÚBLICAS (FORNECEDOR) ====================

@app.route('/')
def index():
    return render_template('fornecedor_entrada.html')

@app.route('/verificar-codigo', methods=['POST'])
def verificar_codigo():
    codigo = request.form.get('codigo', '').strip().upper()
    if not codigo:
        flash('Informe o código do fornecedor.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    fornecedor = conn.execute(
        'SELECT * FROM fornecedores WHERE codigo = ? AND ativo = 1', (codigo,)
    ).fetchone()
    conn.close()

    if not fornecedor:
        flash('Código de fornecedor não encontrado ou inativo. Verifique com o comprador.', 'error')
        return redirect(url_for('index'))

    session['fornecedor_id'] = fornecedor['id']
    session['fornecedor_codigo'] = fornecedor['codigo']
    return redirect(url_for('formulario_cotacao'))

@app.route('/cotacao')
def formulario_cotacao():
    if 'fornecedor_id' not in session:
        flash('Acesse com seu código de fornecedor.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    fornecedor = conn.execute(
        'SELECT * FROM fornecedores WHERE id = ?', (session['fornecedor_id'],)
    ).fetchone()
    conn.close()

    if not fornecedor:
        session.clear()
        flash('Fornecedor não encontrado.', 'error')
        return redirect(url_for('index'))

    return render_template(
        'fornecedor_cotacao.html',
        fornecedor=fornecedor,
        produtos=PRODUTOS,
        condicoes=CONDICOES_PAGAMENTO
    )

@app.route('/enviar-cotacao', methods=['POST'])
def enviar_cotacao():
    if 'fornecedor_id' not in session:
        flash('Sessão expirada. Acesse novamente com seu código.', 'error')
        return redirect(url_for('index'))

    responsavel = request.form.get('responsavel', '').strip()
    prazo_entrega = request.form.get('prazo_entrega', '').strip()
    condicao = request.form.get('condicao_pagamento', '').strip()
    observacoes = request.form.get('observacoes', '').strip()

    if not responsavel or not prazo_entrega or not condicao:
        flash('Preencha todos os campos obrigatórios.', 'error')
        return redirect(url_for('formulario_cotacao'))

    # Coletar preços
    itens = []
    total_geral = 0.0

    for p in PRODUTOS:
        preco_str = request.form.get(f'preco_{p["id"]}', '').strip().replace(',', '.')
        if preco_str:
            try:
                preco_unit = float(preco_str)
                if preco_unit < 0:
                    continue
                preco_total = preco_unit * p['qtd']
                total_geral += preco_total
                itens.append({
                    'produto_id': p['id'],
                    'descricao': p['descricao'],
                    'embalagem': p['embalagem'],
                    'quantidade': p['qtd'],
                    'unidade': p['unidade'],
                    'preco_unitario': preco_unit,
                    'preco_total': preco_total
                })
            except ValueError:
                continue

    if not itens:
        flash('Informe pelo menos um preço.', 'error')
        return redirect(url_for('formulario_cotacao'))

    conn = get_db()
    c = conn.cursor()

    c.execute('''
        INSERT INTO cotacoes (fornecedor_id, responsavel, prazo_entrega, condicao_pagamento, observacoes, total_geral)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session['fornecedor_id'], responsavel, prazo_entrega, condicao, observacoes, total_geral))

    cotacao_id = c.lastrowid

    for item in itens:
        c.execute('''
            INSERT INTO cotacao_itens (cotacao_id, produto_id, descricao, embalagem, quantidade, unidade, preco_unitario, preco_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cotacao_id, item['produto_id'], item['descricao'], item['embalagem'],
              item['quantidade'], item['unidade'], item['preco_unitario'], item['preco_total']))

    conn.commit()
    conn.close()

    session.clear()
    return render_template('sucesso.html', total=total_geral)

# ==================== ROTAS ADMIN ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = get_db()
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin['password_hash'], password):
            user = Admin(admin['id'], admin['username'])
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuário ou senha incorretos.', 'error')

    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db()
    total_fornecedores = conn.execute('SELECT COUNT(*) as c FROM fornecedores WHERE ativo = 1').fetchone()['c']
    total_cotacoes = conn.execute('SELECT COUNT(*) as c FROM cotacoes').fetchone()['c']
    ultimas = conn.execute('''
        SELECT c.id, c.criado_em, c.total_geral, c.responsavel, f.razao_social, f.codigo
        FROM cotacoes c
        JOIN fornecedores f ON f.id = c.fornecedor_id
        ORDER BY c.criado_em DESC LIMIT 10
    ''').fetchall()
    conn.close()
    return render_template('admin_dashboard.html',
                           total_fornecedores=total_fornecedores,
                           total_cotacoes=total_cotacoes,
                           ultimas=ultimas)

# ---- Fornecedores ----

@app.route('/admin/fornecedores')
@login_required
def admin_fornecedores():
    conn = get_db()
    fornecedores = conn.execute('SELECT * FROM fornecedores ORDER BY razao_social').fetchall()
    conn.close()
    return render_template('admin_fornecedores.html', fornecedores=fornecedores)

@app.route('/admin/fornecedores/novo', methods=['GET', 'POST'])
@login_required
def admin_fornecedor_novo():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        razao = request.form.get('razao_social', '').strip()
        cnpj = request.form.get('cnpj', '').strip()
        contato = request.form.get('contato', '').strip()
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()

        if not codigo or not razao:
            flash('Código e Razão Social são obrigatórios.', 'error')
            return redirect(url_for('admin_fornecedor_novo'))

        conn = get_db()
        try:
            conn.execute('''
                INSERT INTO fornecedores (codigo, razao_social, cnpj, contato, telefone, email)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (codigo, razao, cnpj, contato, telefone, email))
            conn.commit()
            flash(f'Fornecedor {razao} cadastrado com sucesso! Código: {codigo}', 'success')
        except sqlite3.IntegrityError:
            flash('Já existe um fornecedor com este código.', 'error')
        finally:
            conn.close()
        return redirect(url_for('admin_fornecedores'))

    return render_template('admin_fornecedor_form.html', fornecedor=None)

@app.route('/admin/fornecedores/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def admin_fornecedor_editar(id):
    conn = get_db()
    fornecedor = conn.execute('SELECT * FROM fornecedores WHERE id = ?', (id,)).fetchone()
    if not fornecedor:
        conn.close()
        flash('Fornecedor não encontrado.', 'error')
        return redirect(url_for('admin_fornecedores'))

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        razao = request.form.get('razao_social', '').strip()
        cnpj = request.form.get('cnpj', '').strip()
        contato = request.form.get('contato', '').strip()
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        ativo = 1 if request.form.get('ativo') else 0

        try:
            conn.execute('''
                UPDATE fornecedores SET codigo=?, razao_social=?, cnpj=?, contato=?, telefone=?, email=?, ativo=?
                WHERE id=?
            ''', (codigo, razao, cnpj, contato, telefone, email, ativo, id))
            conn.commit()
            flash('Fornecedor atualizado com sucesso!', 'success')
        except sqlite3.IntegrityError:
            flash('Já existe outro fornecedor com este código.', 'error')
        finally:
            conn.close()
        return redirect(url_for('admin_fornecedores'))

    conn.close()
    return render_template('admin_fornecedor_form.html', fornecedor=fornecedor)

@app.route('/admin/fornecedores/<int:id>/excluir', methods=['POST'])
@login_required
def admin_fornecedor_excluir(id):
    conn = get_db()
    conn.execute('UPDATE fornecedores SET ativo = 0 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Fornecedor desativado.', 'success')
    return redirect(url_for('admin_fornecedores'))

# ---- Cotações e Comparativo ----

@app.route('/admin/cotacoes')
@login_required
def admin_cotacoes():
    conn = get_db()
    cotacoes = conn.execute('''
        SELECT c.*, f.razao_social, f.codigo
        FROM cotacoes c
        JOIN fornecedores f ON f.id = c.fornecedor_id
        ORDER BY c.criado_em DESC
    ''').fetchall()
    conn.close()
    return render_template('admin_cotacoes.html', cotacoes=cotacoes)

@app.route('/admin/cotacoes/<int:id>')
@login_required
def admin_cotacao_detalhe(id):
    conn = get_db()
    cotacao = conn.execute('''
        SELECT c.*, f.razao_social, f.codigo, f.cnpj, f.telefone, f.email
        FROM cotacoes c
        JOIN fornecedores f ON f.id = c.fornecedor_id
        WHERE c.id = ?
    ''', (id,)).fetchone()

    if not cotacao:
        conn.close()
        flash('Cotação não encontrada.', 'error')
        return redirect(url_for('admin_cotacoes'))

    itens = conn.execute(
        'SELECT * FROM cotacao_itens WHERE cotacao_id = ? ORDER BY produto_id', (id,)
    ).fetchall()
    conn.close()
    return render_template('admin_cotacao_detalhe.html', cotacao=cotacao, itens=itens)

@app.route('/admin/comparativo')
@login_required
def admin_comparativo():
    conn = get_db()

    # Todas as cotações com fornecedor
    cotacoes = conn.execute('''
        SELECT c.id, c.total_geral, c.criado_em, c.responsavel, c.prazo_entrega, c.condicao_pagamento,
               f.razao_social, f.codigo
        FROM cotacoes c
        JOIN fornecedores f ON f.id = c.fornecedor_id
        ORDER BY c.criado_em DESC
    ''').fetchall()

    # Itens de todas as cotações
    itens = conn.execute('''
        SELECT ci.*, c.fornecedor_id, f.razao_social, f.codigo
        FROM cotacao_itens ci
        JOIN cotacoes c ON c.id = ci.cotacao_id
        JOIN fornecedores f ON f.id = c.fornecedor_id
        ORDER BY ci.produto_id, ci.preco_unitario
    ''').fetchall()
    conn.close()

    # Organizar por produto
    comparativo = {}
    for p in PRODUTOS:
        comparativo[p['id']] = {
            'produto': p,
            'ofertas': []
        }

    for item in itens:
        pid = item['produto_id']
        if pid in comparativo:
            comparativo[pid]['ofertas'].append(item)

    # Calcular vencedor por produto
    for pid, data in comparativo.items():
        if data['ofertas']:
            data['melhor'] = min(data['ofertas'], key=lambda x: x['preco_unitario'])
        else:
            data['melhor'] = None

    return render_template('admin_comparativo.html',
                           comparativo=comparativo,
                           cotacoes=cotacoes,
                           produtos=PRODUTOS)

# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    init_db()
