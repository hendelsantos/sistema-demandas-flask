from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime
import uuid
from sqlalchemy import func, extract
from dotenv import load_dotenv
import pymysql

# Instalar PyMySQL como MySQLdb
pymysql.install_as_MySQLdb()

# Carregar variáveis de ambiente
load_dotenv()

# Importar módulo da rede social
from rede_social import registrar_rotas_rede_social

# Importar módulo PM05
from pm05 import registrar_rotas_pm05

# Importar módulo GI
from gi import registrar_rotas_gi

app = Flask(__name__)

# Configuração do banco de dados
if os.getenv('MYSQL_HOST'):
    # Configuração MySQL
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_database = os.getenv('MYSQL_DATABASE', 'sistema_demandas')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
    print("🔗 Conectando ao MySQL...")
else:
    # Fallback para SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demandas.db'
    print("🔗 Conectando ao SQLite...")

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui')
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
    
    # Campos para organização anual
    ano_orcamentario = db.Column(db.Integer, default=lambda: datetime.utcnow().year)
    numero_demanda = db.Column(db.String(20), unique=True)  # Ex: 2025-001, 2025-002
    
    # Datas de follow-up para cada etapa do processo
    data_aberto = db.Column(db.DateTime, default=datetime.utcnow)  # Data que foi criada (Aberto)
    data_em_cotacao = db.Column(db.DateTime)  # Data que entrou em cotação
    data_cotacao_aprovada = db.Column(db.DateTime)  # Data que a cotação foi aprovada
    data_po_emitido = db.Column(db.DateTime)  # Data que o PO foi emitido
    data_produto_recebido = db.Column(db.DateTime)  # Data que o produto foi recebido
    data_nf_recebida = db.Column(db.DateTime)  # Data que a NF foi recebida
    
    # Relacionamentos
    arquivos = db.relationship('ArquivoDemanda', backref='demanda', lazy=True, cascade='all, delete-orphan')
    pedido = db.relationship('Pedido', backref='demanda', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Definir ano orçamentário se não foi fornecido
        if not self.ano_orcamentario:
            self.ano_orcamentario = datetime.utcnow().year
    
    @staticmethod
    def gerar_proximo_numero_demanda(ano=None):
        """Gera próximo número sequencial da demanda para o ano"""
        if ano is None:
            ano = datetime.utcnow().year
        
        # Buscar último número do ano
        ultima_demanda = Demanda.query.filter_by(ano_orcamentario=ano).order_by(Demanda.id.desc()).first()
        
        if ultima_demanda and ultima_demanda.numero_demanda:
            try:
                ultimo_numero = int(ultima_demanda.numero_demanda.split('-')[1])
                proximo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                proximo_numero = 1
        else:
            proximo_numero = 1
            
        return f"{ano}-{proximo_numero:03d}"

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

# Context processor para disponibilizar variáveis globais nos templates
@app.context_processor
def inject_user():
    """Injeta informações do usuário atual nos templates"""
    current_user = None
    if 'user_id' in session:
        current_user = Usuario.query.get(session['user_id'])
    return dict(current_user=current_user)

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
    # Filtro de ano - padrão é o ano atual
    ano_atual = datetime.utcnow().year
    ano_filtro = request.args.get('ano', ano_atual, type=int)
    
    # Estatísticas do ano selecionado
    total_demandas = Demanda.query.filter_by(ano_orcamentario=ano_filtro).count()
    demandas_abertas = Demanda.query.filter_by(ano_orcamentario=ano_filtro, status='Aberto').count()
    demandas_cotacao = Demanda.query.filter_by(ano_orcamentario=ano_filtro, status='Em Cotação').count()
    demandas_pr = Demanda.query.filter_by(ano_orcamentario=ano_filtro, status='PR Criada').count()
    demandas_po = Demanda.query.filter_by(ano_orcamentario=ano_filtro, status='PO Emitido').count()
    demandas_nf = Demanda.query.filter_by(ano_orcamentario=ano_filtro, status='NF Recebida').count()
    
    # Lista de anos disponíveis para o filtro
    anos_disponiveis = db.session.query(Demanda.ano_orcamentario).distinct().order_by(Demanda.ano_orcamentario.desc()).all()
    anos_disponiveis = [ano[0] for ano in anos_disponiveis if ano[0] is not None]
    
    # Se não há demandas ainda, incluir o ano atual
    if not anos_disponiveis:
        anos_disponiveis = [ano_atual]
    
    return render_template('dashboard.html', 
                         total_demandas=total_demandas,
                         demandas_abertas=demandas_abertas,
                         demandas_cotacao=demandas_cotacao,
                         demandas_pr=demandas_pr,
                         demandas_po=demandas_po,
                         demandas_nf=demandas_nf,
                         ano_filtro=ano_filtro,
                         anos_disponiveis=anos_disponiveis,
                         ano_atual=ano_atual)

@app.route('/nova_demanda', methods=['GET', 'POST'])
def nova_demanda():
    if request.method == 'POST':
        # Criar a demanda
        demanda = Demanda(
            solicitante=request.form['solicitante'],
            descricao_item=request.form['descricao_item'],
            quantidade=int(request.form['quantidade']),
            catalog=request.form.get('catalog', ''),
            onde_utilizado=request.form['onde_utilizado'],
            justificativa=request.form['justificativa']
        )
        
        # Gerar número da demanda
        demanda.numero_demanda = Demanda.gerar_proximo_numero_demanda(demanda.ano_orcamentario)
        
        db.session.add(demanda)
        db.session.commit()
        
        flash('Demanda criada com sucesso!', 'success')
        return redirect(url_for('listar_demandas'))
    
    return render_template('nova_demanda.html')

@app.route('/demandas')
def listar_demandas():
    # Filtros
    status_filter = request.args.get('status', '')
    ano_atual = datetime.utcnow().year
    ano_filter = request.args.get('ano', ano_atual, type=int)
    
    # Query base
    query = Demanda.query.filter_by(ano_orcamentario=ano_filter)
    
    # Aplicar filtro de status se especificado
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    demandas = query.order_by(Demanda.data_criacao.desc()).all()
    
    # Anos disponíveis para o filtro
    anos_disponiveis = db.session.query(Demanda.ano_orcamentario).distinct().order_by(Demanda.ano_orcamentario.desc()).all()
    anos_disponiveis = [ano[0] for ano in anos_disponiveis if ano[0] is not None]
    
    if not anos_disponiveis:
        anos_disponiveis = [ano_atual]
    
    return render_template('listar_demandas.html', 
                         demandas=demandas, 
                         status_filter=status_filter,
                         ano_filter=ano_filter,
                         anos_disponiveis=anos_disponiveis,
                         ano_atual=ano_atual)

@app.route('/demanda/<int:id>')
def detalhes_demanda(id):
    demanda = Demanda.query.get_or_404(id)
    return render_template('detalhes_demanda.html', demanda=demanda)

@app.route('/atualizar_status/<int:id>', methods=['POST'])
@admin_required
def atualizar_status(id):
    demanda = Demanda.query.get_or_404(id)
    novo_status = request.form['status']
    
    # Atualizar data específica baseada no novo status
    agora = datetime.utcnow()
    
    if novo_status == 'Em Cotação' and not demanda.data_em_cotacao:
        demanda.data_em_cotacao = agora
    elif novo_status == 'Cotação Aprovada' and not demanda.data_cotacao_aprovada:
        demanda.data_cotacao_aprovada = agora
    elif novo_status == 'PO Emitido' and not demanda.data_po_emitido:
        demanda.data_po_emitido = agora
    elif novo_status == 'Produto Recebido' and not demanda.data_produto_recebido:
        demanda.data_produto_recebido = agora
    elif novo_status == 'NF Recebida' and not demanda.data_nf_recebida:
        demanda.data_nf_recebida = agora
    
    demanda.status = novo_status
    demanda.data_atualizacao = agora
    
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
        
        # Atualizar status da demanda e data de follow-up
        agora = datetime.utcnow()
        demanda.status = 'PO Emitido'
        demanda.data_atualizacao = agora
        if not demanda.data_po_emitido:
            demanda.data_po_emitido = agora
        
        db.session.commit()
        
        flash('Pedido criado com sucesso!', 'success')
        return redirect(url_for('listar_pedidos'))
    
    return render_template('novo_pedido.html', demanda=demanda)

@app.route('/confirmar_recebimento/<int:pedido_id>', methods=['POST'])
@admin_required
def confirmar_recebimento(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    
    agora = datetime.utcnow()
    pedido.data_recebimento = agora
    pedido.valor_recebido = float(request.form['valor_recebido']) if request.form['valor_recebido'] else pedido.valor_total
    
    # Atualizar data de follow-up da demanda
    demanda = pedido.demanda
    if not demanda.data_produto_recebido:
        demanda.data_produto_recebido = agora
        demanda.status = 'Produto Recebido'
        demanda.data_atualizacao = agora
    
    db.session.commit()
    
    flash('Recebimento confirmado com sucesso!', 'success')
    return redirect(url_for('listar_pedidos'))

@app.route('/confirmar_recebimento_nf/<int:pedido_id>', methods=['POST'])
@admin_required
def confirmar_recebimento_nf(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    
    agora = datetime.utcnow()
    # Atualizar dados da Nota Fiscal
    pedido.numero_nota_fiscal = request.form['numero_nota_fiscal']
    pedido.data_recebimento_nf = agora
    
    # Atualizar status da demanda para "NF Recebida" e data de follow-up
    demanda = pedido.demanda
    demanda.status = 'NF Recebida'
    demanda.data_atualizacao = agora
    if not demanda.data_nf_recebida:
        demanda.data_nf_recebida = agora
    
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

# ==================== NOVAS FUNCIONALIDADES ANUAIS ====================

@app.route('/metricas-anuais')
def metricas_anuais():
    """Métricas comparativas entre anos"""
    anos_selecionados = request.args.getlist('anos', type=int)
    ano_atual = datetime.utcnow().year
    
    # Se nenhum ano foi selecionado, usar os últimos 3 anos
    if not anos_selecionados:
        anos_selecionados = [ano_atual - 2, ano_atual - 1, ano_atual]
    
    # Anos disponíveis
    anos_disponiveis = db.session.query(Demanda.ano_orcamentario).distinct().order_by(Demanda.ano_orcamentario.desc()).all()
    anos_disponiveis = [ano[0] for ano in anos_disponiveis if ano[0] is not None]
    
    if not anos_disponiveis:
        anos_disponiveis = [ano_atual]
    
    dados_comparativos = {}
    
    for ano in anos_selecionados:
        # Estatísticas básicas do ano
        total_demandas = Demanda.query.filter_by(ano_orcamentario=ano).count()
        demandas_finalizadas = Demanda.query.filter_by(ano_orcamentario=ano, status='NF Recebida').count()
        
        # Valores financeiros
        valor_total_pedidos = db.session.query(func.sum(Pedido.valor_total)).join(Demanda).filter(
            Demanda.ano_orcamentario == ano,
            Pedido.valor_total.isnot(None)
        ).scalar() or 0
        
        valor_total_recebido = db.session.query(func.sum(Pedido.valor_recebido)).join(Demanda).filter(
            Demanda.ano_orcamentario == ano,
            Pedido.valor_recebido.isnot(None)
        ).scalar() or 0
        
        # Performance por mês
        demandas_por_mes = db.session.query(
            extract('month', Demanda.data_criacao).label('mes'),
            func.count(Demanda.id).label('total')
        ).filter(Demanda.ano_orcamentario == ano).group_by('mes').all()
        
        # Organizar dados mensais
        meses_dados = {i: 0 for i in range(1, 13)}
        for mes, total in demandas_por_mes:
            meses_dados[int(mes)] = total
        
        dados_comparativos[ano] = {
            'total_demandas': total_demandas,
            'demandas_finalizadas': demandas_finalizadas,
            'taxa_finalizacao': round((demandas_finalizadas / total_demandas * 100) if total_demandas > 0 else 0, 1),
            'valor_total_pedidos': valor_total_pedidos,
            'valor_total_recebido': valor_total_recebido,
            'economia_gerada': valor_total_pedidos - valor_total_recebido,
            'demandas_por_mes': list(meses_dados.values())
        }
    
    return render_template('metricas_anuais.html', 
                         dados=dados_comparativos,
                         anos_selecionados=anos_selecionados,
                         anos_disponiveis=anos_disponiveis,
                         ano_atual=ano_atual)

@app.route('/relatorio-fechamento/<int:ano>')
@admin_required
def relatorio_fechamento_anual(ano):
    """Relatório completo de fechamento anual"""
    
    # Estatísticas gerais
    total_demandas = Demanda.query.filter_by(ano_orcamentario=ano).count()
    demandas_finalizadas = Demanda.query.filter_by(ano_orcamentario=ano, status='NF Recebida').count()
    demandas_pendentes = total_demandas - demandas_finalizadas
    
    # Valores financeiros
    valor_total_orcado = db.session.query(func.sum(Pedido.valor_total)).join(Demanda).filter(
        Demanda.ano_orcamentario == ano,
        Pedido.valor_total.isnot(None)
    ).scalar() or 0
    
    valor_total_realizado = db.session.query(func.sum(Pedido.valor_recebido)).join(Demanda).filter(
        Demanda.ano_orcamentario == ano,
        Pedido.valor_recebido.isnot(None)
    ).scalar() or 0
    
    economia_gerada = valor_total_orcado - valor_total_realizado
    
    # Demandas por status
    demandas_por_status_raw = db.session.query(
        Demanda.status,
        func.count(Demanda.id).label('total')
    ).filter(Demanda.ano_orcamentario == ano).group_by(Demanda.status).all()
    
    # Converter para dicionário serializável
    demandas_por_status = {row[0]: row[1] for row in demandas_por_status_raw}
    
    # Top solicitantes
    top_solicitantes_raw = db.session.query(
        Demanda.solicitante,
        func.count(Demanda.id).label('total_demandas'),
        func.sum(Pedido.valor_total).label('valor_total')
    ).join(Pedido, Demanda.id == Pedido.demanda_id, isouter=True).filter(
        Demanda.ano_orcamentario == ano
    ).group_by(Demanda.solicitante).order_by(func.count(Demanda.id).desc()).limit(10).all()
    
    # Converter para lista de dicionários serializáveis
    top_solicitantes = [
        {
            'solicitante': row[0],
            'total_demandas': row[1],
            'valor_total': float(row[2]) if row[2] else 0.0
        }
        for row in top_solicitantes_raw
    ]
    
    # Performance mensal
    performance_mensal_raw = db.session.query(
        extract('month', Demanda.data_criacao).label('mes'),
        func.count(Demanda.id).label('total_demandas'),
        func.sum(Pedido.valor_total).label('valor_orcado')
    ).join(Pedido, Demanda.id == Pedido.demanda_id, isouter=True).filter(
        Demanda.ano_orcamentario == ano
    ).group_by('mes').order_by('mes').all()
    
    # Converter para lista de dicionários serializáveis
    performance_mensal = [
        {
            'mes': int(row[0]) if row[0] else 0,
            'total_demandas': row[1],
            'valor_orcado': float(row[2]) if row[2] else 0.0
        }
        for row in performance_mensal_raw
    ]
    
    # Demandas que ficaram pendentes
    demandas_pendentes_lista = Demanda.query.filter(
        Demanda.ano_orcamentario == ano,
        Demanda.status != 'NF Recebida'
    ).order_by(Demanda.data_criacao.desc()).limit(20).all()
    
    relatorio = {
        'ano': ano,
        'periodo': f"01/01/{ano} a 31/12/{ano}",
        'resumo_geral': {
            'total_demandas': total_demandas,
            'demandas_finalizadas': demandas_finalizadas,
            'demandas_pendentes': demandas_pendentes,
            'taxa_finalizacao': round((demandas_finalizadas / total_demandas * 100) if total_demandas > 0 else 0, 1),
            'valor_total_orcado': valor_total_orcado,
            'valor_total_realizado': valor_total_realizado,
            'economia_gerada': economia_gerada,
            'percentual_economia': round((economia_gerada / valor_total_orcado * 100) if valor_total_orcado > 0 else 0, 1)
        },
        'demandas_por_status': demandas_por_status,
        'top_solicitantes': top_solicitantes,
        'performance_mensal': performance_mensal,
        'demandas_pendentes_lista': demandas_pendentes_lista
    }
    
    return render_template('relatorio_fechamento.html', relatorio=relatorio)

@app.route('/api/comparativo-anos')
def api_comparativo_anos():
    """API para dados de comparativo entre anos"""
    anos = request.args.getlist('anos', type=int)
    
    if not anos:
        ano_atual = datetime.utcnow().year
        anos = [ano_atual - 2, ano_atual - 1, ano_atual]
    
    dados = {}
    
    for ano in anos:
        # Demandas por mês
        demandas_mes = db.session.query(
            extract('month', Demanda.data_criacao).label('mes'),
            func.count(Demanda.id).label('total')
        ).filter(Demanda.ano_orcamentario == ano).group_by('mes').all()
        
        # Valores por mês
        valores_mes = db.session.query(
            extract('month', Demanda.data_criacao).label('mes'),
            func.sum(Pedido.valor_total).label('valor')
        ).join(Pedido, Demanda.id == Pedido.demanda_id, isouter=True).filter(
            Demanda.ano_orcamentario == ano
        ).group_by('mes').all()
        
        # Organizar dados
        meses_demandas = {i: 0 for i in range(1, 13)}
        meses_valores = {i: 0 for i in range(1, 13)}
        
        for mes, total in demandas_mes:
            meses_demandas[int(mes)] = total
            
        for mes, valor in valores_mes:
            meses_valores[int(mes)] = float(valor or 0)
        
        dados[ano] = {
            'demandas': list(meses_demandas.values()),
            'valores': list(meses_valores.values())
        }
    
    return jsonify(dados)

# ==================== FIM NOVAS FUNCIONALIDADES ====================

# Função helper para formatar data no template
@app.template_filter('format_date')
def format_date(date):
    if date:
        return date.strftime('%d/%m/%Y às %H:%M')
    return 'Não informado'

# Função helper para obter histórico de follow-up
def obter_historico_followup(demanda):
    """Retorna lista ordenada com o histórico de follow-up da demanda"""
    historico = []
    
    if demanda.data_aberto:
        historico.append({
            'status': 'Aberto',
            'data': demanda.data_aberto,
            'icone': 'fa-plus-circle',
            'cor': 'primary'
        })
    
    if demanda.data_em_cotacao:
        historico.append({
            'status': 'Em Cotação',
            'data': demanda.data_em_cotacao,
            'icone': 'fa-search-dollar',
            'cor': 'warning'
        })
    
    if demanda.data_cotacao_aprovada:
        historico.append({
            'status': 'Cotação Aprovada',
            'data': demanda.data_cotacao_aprovada,
            'icone': 'fa-check-circle',
            'cor': 'info'
        })
    
    if demanda.data_po_emitido:
        historico.append({
            'status': 'PO Emitido',
            'data': demanda.data_po_emitido,
            'icone': 'fa-file-invoice',
            'cor': 'primary'
        })
    
    if demanda.data_produto_recebido:
        historico.append({
            'status': 'Produto Recebido',
            'data': demanda.data_produto_recebido,
            'icone': 'fa-box-open',
            'cor': 'success'
        })
    
    if demanda.data_nf_recebida:
        historico.append({
            'status': 'NF Recebida',
            'data': demanda.data_nf_recebida,
            'icone': 'fa-receipt',
            'cor': 'success'
        })
    
    # Ordenar por data
    historico.sort(key=lambda x: x['data'])
    return historico

# Disponibilizar função para templates
app.jinja_env.globals.update(obter_historico_followup=obter_historico_followup)

def criar_usuario_admin():
    """Criar usuário admin padrão se não existir"""
    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        admin = Usuario(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Usuário admin criado com sucesso!")

# Registrar rotas da rede social
with app.app_context():
    registrar_rotas_rede_social(app, db)

# Registrar rotas do PM05
with app.app_context():
    registrar_rotas_pm05(app, db)

# Registrar rotas do GI
with app.app_context():
    registrar_rotas_gi(app, db)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_usuario_admin()
    app.run(debug=True, port=5003)
