from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demandas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Criar pasta de uploads se não existir
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelos do banco de dados
class Demanda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solicitante = db.Column(db.String(100), nullable=False)
    descricao_item = db.Column(db.Text, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    catalog = db.Column(db.String(100))
    onde_utilizado = db.Column(db.String(200), nullable=False)
    justificativa = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Aberto')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    arquivos = db.relationship('ArquivoDemanda', backref='demanda', lazy=True, cascade='all, delete-orphan')
    pedido = db.relationship('Pedido', backref='demanda', uselist=False, cascade='all, delete-orphan')

class ArquivoDemanda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    demanda_id = db.Column(db.Integer, db.ForeignKey('demanda.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    nome_original = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)  # cotacao, po, etc
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    demanda_id = db.Column(db.Integer, db.ForeignKey('demanda.id'), nullable=False)
    numero_po = db.Column(db.String(100))
    numero_nota_fiscal = db.Column(db.String(100))
    valor_total = db.Column(db.Float)
    mes_previsto_recebimento = db.Column(db.String(7))  # YYYY-MM
    data_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    data_recebimento = db.Column(db.DateTime)  # Data de recebimento do produto/material
    data_recebimento_nf = db.Column(db.DateTime)  # Data de recebimento da Nota Fiscal
    valor_recebido = db.Column(db.Float)
    fornecedor = db.Column(db.String(200))

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Decorador para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar se é admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('login'))
        
        user = Usuario.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Acesso negado. Esta área é restrita a administradores.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas principais
@app.route('/')
def index():
    # Home agora é a lista de demandas
    return redirect(url_for('listar_demandas'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Usuario.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            flash(f'Bem-vindo, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    total_demandas = Demanda.query.count()
    demandas_abertas = Demanda.query.filter_by(status='Aberto').count()
    demandas_cotacao = Demanda.query.filter_by(status='Em Cotação').count()
    demandas_pr = Demanda.query.filter_by(status='PR Criada').count()
    demandas_po = Demanda.query.filter_by(status='PO Emitido').count()
    demandas_nf = Demanda.query.filter_by(status='NF Recebida').count()
    
    return render_template('dashboard.html', 
                         total_demandas=total_demandas,
                         demandas_abertas=demandas_abertas,
                         demandas_cotacao=demandas_cotacao,
                         demandas_pr=demandas_pr,
                         demandas_po=demandas_po,
                         demandas_nf=demandas_nf)

@app.route('/nova_demanda', methods=['GET', 'POST'])
def nova_demanda():
    if request.method == 'POST':
        demanda = Demanda(
            solicitante=request.form['solicitante'],
            descricao_item=request.form['descricao_item'],
            quantidade=int(request.form['quantidade']),
            catalog=request.form.get('catalog', ''),
            onde_utilizado=request.form['onde_utilizado'],
            justificativa=request.form['justificativa']
        )
        
        db.session.add(demanda)
        db.session.commit()
        
        flash('Demanda criada com sucesso!', 'success')
        return redirect(url_for('listar_demandas'))
    
    return render_template('nova_demanda.html')

@app.route('/demandas')
def listar_demandas():
    status_filter = request.args.get('status', '')
    if status_filter:
        demandas = Demanda.query.filter_by(status=status_filter).order_by(Demanda.data_criacao.desc()).all()
    else:
        demandas = Demanda.query.order_by(Demanda.data_criacao.desc()).all()
    
    return render_template('listar_demandas.html', demandas=demandas, status_filter=status_filter)

@app.route('/demanda/<int:id>')
def detalhes_demanda(id):
    demanda = Demanda.query.get_or_404(id)
    return render_template('detalhes_demanda.html', demanda=demanda)

@app.route('/atualizar_status/<int:id>', methods=['POST'])
@admin_required
def atualizar_status(id):
    demanda = Demanda.query.get_or_404(id)
    novo_status = request.form['status']
    
    demanda.status = novo_status
    demanda.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    flash(f'Status atualizado para: {novo_status}', 'success')
    
    return redirect(url_for('detalhes_demanda', id=id))

@app.route('/editar_demanda/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_demanda(id):
    demanda = Demanda.query.get_or_404(id)
    
    if request.method == 'POST':
        demanda.solicitante = request.form['solicitante']
        demanda.descricao_item = request.form['descricao_item']
        demanda.quantidade = int(request.form['quantidade'])
        demanda.catalog = request.form.get('catalog', '')
        demanda.onde_utilizado = request.form['onde_utilizado']
        demanda.justificativa = request.form['justificativa']
        demanda.data_atualizacao = datetime.utcnow()
        
        db.session.commit()
        flash('Demanda atualizada com sucesso!', 'success')
        return redirect(url_for('detalhes_demanda', id=id))
    
    return render_template('editar_demanda.html', demanda=demanda)

@app.route('/deletar_demanda/<int:id>', methods=['POST'])
@admin_required
def deletar_demanda(id):
    demanda = Demanda.query.get_or_404(id)
    
    # Deletar arquivos físicos associados
    for arquivo in demanda.arquivos:
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.nome_arquivo)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
    
    db.session.delete(demanda)
    db.session.commit()
    
    flash('Demanda deletada com sucesso!', 'success')
    return redirect(url_for('listar_demandas'))

@app.route('/upload_arquivo/<int:demanda_id>', methods=['POST'])
def upload_arquivo(demanda_id):
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('detalhes_demanda', id=demanda_id))
    
    arquivo = request.files['arquivo']
    tipo_arquivo = request.form['tipo_arquivo']
    
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('detalhes_demanda', id=demanda_id))
    
    if arquivo and arquivo.filename.lower().endswith('.pdf'):
        # Gerar nome único para o arquivo
        nome_arquivo = str(uuid.uuid4()) + '.pdf'
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
        arquivo.save(caminho_arquivo)
        
        # Salvar no banco de dados
        arquivo_db = ArquivoDemanda(
            demanda_id=demanda_id,
            nome_arquivo=nome_arquivo,
            nome_original=arquivo.filename,
            tipo_arquivo=tipo_arquivo
        )
        
        db.session.add(arquivo_db)
        db.session.commit()
        
        flash('Arquivo enviado com sucesso!', 'success')
    else:
        flash('Apenas arquivos PDF são permitidos', 'error')
    
    return redirect(url_for('detalhes_demanda', id=demanda_id))

@app.route('/download_arquivo/<int:arquivo_id>')
def download_arquivo(arquivo_id):
    arquivo = ArquivoDemanda.query.get_or_404(arquivo_id)
    caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], arquivo.nome_arquivo)
    return send_file(caminho_arquivo, as_attachment=True, download_name=arquivo.nome_original)

@app.route('/pedidos')
@admin_required
def listar_pedidos():
    pedidos = Pedido.query.join(Demanda).order_by(Pedido.data_pedido.desc()).all()
    return render_template('listar_pedidos.html', pedidos=pedidos)

@app.route('/novo_pedido/<int:demanda_id>', methods=['GET', 'POST'])
@admin_required
def novo_pedido(demanda_id):
    demanda = Demanda.query.get_or_404(demanda_id)
    
    if request.method == 'POST':
        pedido = Pedido(
            demanda_id=demanda_id,
            numero_po=request.form['numero_po'],
            numero_nota_fiscal=request.form.get('numero_nota_fiscal', ''),
            valor_total=float(request.form['valor_total']) if request.form['valor_total'] else None,
            mes_previsto_recebimento=request.form['mes_previsto_recebimento'],
            fornecedor=request.form.get('fornecedor', '')
        )
        
        db.session.add(pedido)
        
        # Atualizar status da demanda
        demanda.status = 'PO Emitido'
        demanda.data_atualizacao = datetime.utcnow()
        
        db.session.commit()
        
        flash('Pedido criado com sucesso!', 'success')
        return redirect(url_for('listar_pedidos'))
    
    return render_template('novo_pedido.html', demanda=demanda)

@app.route('/confirmar_recebimento/<int:pedido_id>', methods=['POST'])
@admin_required
def confirmar_recebimento(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    
    pedido.data_recebimento = datetime.utcnow()
    pedido.valor_recebido = float(request.form['valor_recebido']) if request.form['valor_recebido'] else pedido.valor_total
    
    db.session.commit()
    
    flash('Recebimento confirmado com sucesso!', 'success')
    return redirect(url_for('listar_pedidos'))

@app.route('/confirmar_recebimento_nf/<int:pedido_id>', methods=['POST'])
@admin_required
def confirmar_recebimento_nf(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Atualizar dados da Nota Fiscal
    pedido.numero_nota_fiscal = request.form['numero_nota_fiscal']
    pedido.data_recebimento_nf = datetime.utcnow()
    
    # Atualizar status da demanda para "NF Recebida"
    demanda = pedido.demanda
    demanda.status = 'NF Recebida'
    demanda.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    
    flash('Recebimento da Nota Fiscal confirmado com sucesso!', 'success')
    return redirect(url_for('listar_pedidos'))

@app.route('/metricas')
def metricas():
    # Buscar dados para métricas
    from sqlalchemy import func, extract
    
    # Previsões por mês
    previsoes = db.session.query(
        Pedido.mes_previsto_recebimento,
        func.sum(Pedido.valor_total).label('valor_previsto')
    ).filter(
        Pedido.valor_total.isnot(None),
        Pedido.mes_previsto_recebimento.isnot(None)
    ).group_by(Pedido.mes_previsto_recebimento).all()
    
    # Recebimentos por mês
    recebimentos = db.session.query(
        func.strftime('%Y-%m', Pedido.data_recebimento).label('mes_recebimento'),
        func.sum(Pedido.valor_recebido).label('valor_recebido')
    ).filter(
        Pedido.data_recebimento.isnot(None),
        Pedido.valor_recebido.isnot(None)
    ).group_by(func.strftime('%Y-%m', Pedido.data_recebimento)).all()
    
    return render_template('metricas.html', previsoes=previsoes, recebimentos=recebimentos)

@app.route('/api/metricas_chart')
def api_metricas_chart():
    from sqlalchemy import func
    
    # Dados para gráfico
    previsoes = db.session.query(
        Pedido.mes_previsto_recebimento,
        func.sum(Pedido.valor_total).label('valor_previsto')
    ).filter(
        Pedido.valor_total.isnot(None),
        Pedido.mes_previsto_recebimento.isnot(None)
    ).group_by(Pedido.mes_previsto_recebimento).all()
    
    recebimentos = db.session.query(
        func.strftime('%Y-%m', Pedido.data_recebimento).label('mes_recebimento'),
        func.sum(Pedido.valor_recebido).label('valor_recebido')
    ).filter(
        Pedido.data_recebimento.isnot(None),
        Pedido.valor_recebido.isnot(None)
    ).group_by(func.strftime('%Y-%m', Pedido.data_recebimento)).all()
    
    # Organizar dados
    dados = {}
    
    for mes, valor in previsoes:
        if mes not in dados:
            dados[mes] = {'previsto': 0, 'recebido': 0}
        dados[mes]['previsto'] = float(valor)
    
    for mes, valor in recebimentos:
        if mes not in dados:
            dados[mes] = {'previsto': 0, 'recebido': 0}
        dados[mes]['recebido'] = float(valor)
    
    # Converter para formato do gráfico
    meses = sorted(dados.keys())
    previstos = [dados[mes]['previsto'] for mes in meses]
    recebidos = [dados[mes]['recebido'] for mes in meses]
    
    return jsonify({
        'meses': meses,
        'previstos': previstos,
        'recebidos': recebidos
    })

def criar_usuario_admin():
    """Criar usuário admin padrão se não existir"""
    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        admin = Usuario(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Usuário admin criado com sucesso!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_usuario_admin()
    app.run(debug=True)
