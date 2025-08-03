"""
Módulo PM05 - Sistema de Controle de Equipamentos para Reparo Externo
Controle completo de envio e retorno de equipamentos para fornecedores
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from sqlalchemy import text

# Criar blueprint para PM05
pm05_bp = Blueprint('pm05', __name__)

# Configurações de upload
UPLOAD_FOLDER_PM05 = 'static/uploads/pm05'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Verifica se o arquivo é permitido"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Obtém o tamanho do arquivo"""
    file.seek(0, 2)  # Move para o final
    size = file.tell()
    file.seek(0)  # Volta para o início
    return size

def format_date_safe(date_obj, format_str='%d/%m/%Y'):
    """Formata data de forma segura, tratando strings e objetos datetime"""
    if not date_obj:
        return 'N/A'
    
    if isinstance(date_obj, str):
        try:
            # Tentar converter string para datetime
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
        except ValueError:
            return date_obj  # Retorna a string original se não conseguir converter
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime(format_str)
    
    return str(date_obj)

def format_datetime_safe(datetime_obj, format_str='%d/%m/%Y às %H:%M'):
    """Formata datetime de forma segura"""
    if not datetime_obj:
        return 'N/A'
    
    if isinstance(datetime_obj, str):
        try:
            # Tentar diferentes formatos
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    datetime_obj = datetime.strptime(datetime_obj, fmt)
                    break
                except ValueError:
                    continue
            else:
                return datetime_obj  # Retorna a string original se não conseguir converter
        except:
            return datetime_obj
    
    if hasattr(datetime_obj, 'strftime'):
        return datetime_obj.strftime(format_str)
    
    return str(datetime_obj)

def criar_tabelas_pm05(db):
    """Cria as tabelas necessárias para o PM05"""
    with db.engine.connect() as conn:
        # Tabela principal de PM05
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pm05_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                catalog_envio VARCHAR(100) NOT NULL,
                catalog_ersa VARCHAR(100),
                descricao TEXT NOT NULL,
                spec TEXT,
                motivo TEXT,
                numero_invoice VARCHAR(50) NOT NULL,
                numero_pm05 VARCHAR(50) NOT NULL UNIQUE,
                quantidade INTEGER NOT NULL,
                fornecedor VARCHAR(200) NOT NULL,
                data_envio DATE NOT NULL,
                nf_saida VARCHAR(50),
                observacoes TEXT,
                nf_retorno VARCHAR(50),
                data_retorno DATE,
                valor_reparo DECIMAL(10,2),
                status VARCHAR(20) DEFAULT 'EM_REPARO',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Tabela de anexos
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pm05_anexos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pm05_id INTEGER NOT NULL,
                nome_arquivo VARCHAR(255) NOT NULL,
                nome_original VARCHAR(255) NOT NULL,
                tipo_arquivo VARCHAR(10) NOT NULL,
                tamanho INTEGER NOT NULL,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pm05_id) REFERENCES pm05_items (id)
            )
        """))
        
        # Tabela de histórico
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pm05_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pm05_id INTEGER NOT NULL,
                acao VARCHAR(100) NOT NULL,
                detalhes TEXT,
                usuario VARCHAR(100),
                data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pm05_id) REFERENCES pm05_items (id)
            )
        """))
        
        conn.commit()

class PM05Item:
    """Classe para representar um item PM05"""
    def __init__(self, id, catalog_envio, catalog_ersa, descricao, spec, motivo, 
                 numero_invoice, numero_pm05, quantidade, fornecedor, data_envio,
                 nf_saida, observacoes, nf_retorno, data_retorno, status, 
                 data_criacao, data_atualizacao):
        self.id = id
        self.catalog_envio = catalog_envio
        self.catalog_ersa = catalog_ersa
        self.descricao = descricao
        self.spec = spec
        self.motivo = motivo
        self.numero_invoice = numero_invoice
        self.numero_pm05 = numero_pm05
        self.quantidade = quantidade
        self.fornecedor = fornecedor
        
        # Converter strings para datetime se necessário
        if isinstance(data_envio, str):
            from datetime import datetime
            try:
                self.data_envio = datetime.strptime(data_envio, '%Y-%m-%d').date()
            except:
                self.data_envio = data_envio
        else:
            self.data_envio = data_envio
            
        self.nf_saida = nf_saida
        self.observacoes = observacoes
        self.nf_retorno = nf_retorno
        
        if isinstance(data_retorno, str) and data_retorno:
            try:
                self.data_retorno = datetime.strptime(data_retorno, '%Y-%m-%d').date()
            except:
                self.data_retorno = data_retorno
        else:
            self.data_retorno = data_retorno
            
        self.status = status
        self.data_criacao = data_criacao
        self.data_atualizacao = data_atualizacao
        self.anexos = []

def gerar_numero_pm05():
    """Gera um número único para PM05"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PM05-{timestamp}"

def obter_todos_pm05(db, filtro_status=None, filtro_busca=None):
    """Obtém todos os itens PM05 com filtros opcionais - Otimizado"""
    with db.engine.connect() as conn:
        # Query otimizada com cálculo de dias diretamente no SQL
        query = """
            SELECT id, catalog_envio, catalog_ersa, descricao, spec, motivo,
                   numero_invoice, numero_pm05, quantidade, fornecedor, data_envio,
                   nf_saida, observacoes, nf_retorno, data_retorno, status,
                   data_criacao, data_atualizacao,
                   CASE 
                       WHEN status = 'EM_REPARO' AND data_envio IS NOT NULL 
                       THEN julianday('now') - julianday(data_envio)
                       ELSE 0 
                   END as days_in_repair
            FROM pm05_items
            WHERE 1=1
        """
        params = {}
        
        if filtro_status:
            query += " AND status = :status"
            params["status"] = filtro_status
            
        if filtro_busca:
            query += """ AND (
                descricao LIKE :busca OR 
                numero_pm05 LIKE :busca OR 
                numero_invoice LIKE :busca OR
                fornecedor LIKE :busca OR
                catalog_envio LIKE :busca
            )"""
            params["busca"] = f"%{filtro_busca}%"
            
        query += " ORDER BY data_criacao DESC LIMIT 100"  # Limitar resultados
        
        result = conn.execute(text(query), params)
        items = []
        
        for row in result:
            item = PM05Item(
                id=row[0], catalog_envio=row[1], catalog_ersa=row[2], descricao=row[3],
                spec=row[4], motivo=row[5], numero_invoice=row[6], numero_pm05=row[7],
                quantidade=row[8], fornecedor=row[9], data_envio=row[10],
                nf_saida=row[11], observacoes=row[12], nf_retorno=row[13],
                data_retorno=row[14], status=row[15], data_criacao=row[16],
                data_atualizacao=row[17]
            )
            # Adicionar dias calculados no SQL
            item.days_in_repair = int(row[18]) if row[18] else 0
            items.append(item)
        
        return items

def obter_estatisticas_pm05(db):
    """Obtém estatísticas do PM05 - Otimizado com uma única query"""
    with db.engine.connect() as conn:
        # Query otimizada que calcula tudo de uma vez
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_items,
                SUM(CASE WHEN status = 'EM_REPARO' THEN 1 ELSE 0 END) as em_reparo,
                SUM(CASE WHEN status = 'FINALIZADO' THEN 1 ELSE 0 END) as finalizados
            FROM pm05_items
        """))
        
        row = result.fetchone()
        total_items = row[0]
        em_reparo = row[1]
        finalizados = row[2]
        
        # Top fornecedores (consulta separada apenas se houver dados)
        top_fornecedores = []
        if total_items > 0:
            result = conn.execute(text("""
                SELECT fornecedor, COUNT(*) as total
                FROM pm05_items
                GROUP BY fornecedor
                ORDER BY total DESC
                LIMIT 5
            """))
            top_fornecedores = [{'nome': row[0], 'total': row[1]} for row in result]
        
        return {
            'total_items': total_items,
            'em_reparo': em_reparo,
            'finalizados': finalizados,
            'top_fornecedores': top_fornecedores
        }

def criar_diretorio_uploads_pm05():
    """Cria o diretório de uploads se não existir"""
    if not os.path.exists(UPLOAD_FOLDER_PM05):
        os.makedirs(UPLOAD_FOLDER_PM05, exist_ok=True)

def adicionar_historico(db, pm05_id, acao, detalhes, usuario="Sistema"):
    """Adiciona entrada no histórico"""
    with db.engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO pm05_historico (pm05_id, acao, detalhes, usuario)
            VALUES (:pm05_id, :acao, :detalhes, :usuario)
        """), {
            "pm05_id": pm05_id,
            "acao": acao,
            "detalhes": detalhes,
            "usuario": usuario
        })
        conn.commit()

# Funções para as rotas (serão registradas no app principal)
def registrar_rotas_pm05(app, db):
    """Registra todas as rotas do PM05"""
    
    # Garantir que as tabelas existam
    criar_tabelas_pm05(db)
    criar_diretorio_uploads_pm05()
    
    @app.route('/pm05')
    def listar_pm05():
        """Página principal do PM05"""
        try:
            filtro_status = request.args.get('status')
            filtro_busca = request.args.get('busca')
            
            items = obter_todos_pm05(db, filtro_status, filtro_busca)
            stats = obter_estatisticas_pm05(db)
            
            # Dias já calculados no SQL - remover loop desnecessário
            
            return render_template('pm05.html',
                                 items=items,
                                 stats=stats,
                                 filtro_status=filtro_status,
                                 filtro_busca=filtro_busca,
                                 today_date=datetime.now().strftime('%Y-%m-%d'),
                                 session=session)
        except Exception as e:
            print(f"Erro ao carregar PM05: {e}")
            return render_template('pm05.html',
                                 items=[],
                                 stats={'total_items': 0, 'em_reparo': 0, 'finalizados': 0, 'top_fornecedores': []},
                                 filtro_status=None,
                                 filtro_busca=None,
                                 today_date=datetime.now().strftime('%Y-%m-%d'),
                                 session=session)
    
    @app.route('/pm05/novo')
    def novo_pm05():
        """Formulário para novo item PM05"""
        return render_template('novo_pm05.html', today_date=datetime.now().strftime('%Y-%m-%d'))
    
    @app.route('/pm05/criar', methods=['POST'])
    def criar_pm05():
        """Cria um novo item PM05"""
        try:
            # Validar dados obrigatórios
            campos_obrigatorios = ['catalog_envio', 'descricao', 'numero_invoice', 
                                 'numero_pm05', 'quantidade', 'fornecedor', 'data_envio']
            
            for campo in campos_obrigatorios:
                if not request.form.get(campo):
                    flash(f'Campo {campo} é obrigatório', 'error')
                    return redirect(url_for('novo_pm05'))
            
            # Usar número PM05 do formulário
            numero_pm05 = request.form.get('numero_pm05')
            
            # Inserir no banco
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO pm05_items (
                        catalog_envio, catalog_ersa, descricao, spec, motivo,
                        numero_invoice, numero_pm05, quantidade, fornecedor,
                        data_envio, nf_saida, observacoes, status
                    ) VALUES (
                        :catalog_envio, :catalog_ersa, :descricao, :spec, :motivo,
                        :numero_invoice, :numero_pm05, :quantidade, :fornecedor,
                        :data_envio, :nf_saida, :observacoes, 'EM_REPARO'
                    )
                """), {
                    'catalog_envio': request.form.get('catalog_envio'),
                    'catalog_ersa': request.form.get('catalog_ersa') or None,
                    'descricao': request.form.get('descricao'),
                    'spec': request.form.get('spec') or None,
                    'motivo': request.form.get('motivo') or None,
                    'numero_invoice': request.form.get('numero_invoice'),
                    'numero_pm05': numero_pm05,
                    'quantidade': int(request.form.get('quantidade')),
                    'fornecedor': request.form.get('fornecedor'),
                    'data_envio': request.form.get('data_envio'),
                    'nf_saida': request.form.get('nf_saida') or None,
                    'observacoes': request.form.get('observacoes') or None
                })
                
                # Obter ID do item criado
                pm05_id = result.lastrowid
                conn.commit()
                
                # Adicionar ao histórico
                adicionar_historico(db, pm05_id, "ITEM_CRIADO", 
                                  f"Item PM05 {numero_pm05} criado e enviado para {request.form.get('fornecedor')}")
            
            flash(f'Item PM05 {numero_pm05} criado com sucesso!', 'success')
            return redirect(url_for('listar_pm05'))
            
        except Exception as e:
            print(f"Erro ao criar PM05: {e}")
            flash('Erro ao criar item PM05', 'error')
            return redirect(url_for('novo_pm05'))
    
    @app.route('/pm05/finalizar/<int:item_id>', methods=['POST'])
    def finalizar_pm05(item_id):
        """Finaliza um item PM05 (marca como recebido)"""
        try:
            nf_retorno = request.form.get('nf_retorno')
            observacoes_retorno = request.form.get('observacoes_retorno')
            data_retorno = request.form.get('data_retorno') or datetime.now().strftime('%Y-%m-%d')
            
            with db.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE pm05_items 
                    SET status = 'FINALIZADO',
                        nf_retorno = :nf_retorno,
                        data_retorno = :data_retorno,
                        observacoes = CASE 
                            WHEN observacoes IS NULL THEN :obs_retorno
                            ELSE observacoes || '\n--- RETORNO ---\n' || :obs_retorno
                        END,
                        data_atualizacao = CURRENT_TIMESTAMP
                    WHERE id = :item_id
                """), {
                    'nf_retorno': nf_retorno,
                    'data_retorno': data_retorno,
                    'obs_retorno': observacoes_retorno or 'Item recebido',
                    'item_id': item_id
                })
                conn.commit()
                
                # Adicionar ao histórico
                adicionar_historico(db, item_id, "ITEM_FINALIZADO", 
                                  f"Item recebido de volta. NF: {nf_retorno}")
            
            return jsonify({'success': True})
            
        except Exception as e:
            print(f"Erro ao finalizar PM05: {e}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.route('/pm05/detalhes/<int:item_id>')
    def detalhes_pm05(item_id):
        """Página de detalhes de um item PM05"""
        try:
            with db.engine.connect() as conn:
                # Buscar item
                result = conn.execute(text("""
                    SELECT id, catalog_envio, catalog_ersa, descricao, spec, motivo,
                           numero_invoice, numero_pm05, quantidade, fornecedor, data_envio,
                           nf_saida, observacoes, nf_retorno, data_retorno, status,
                           data_criacao, data_atualizacao
                    FROM pm05_items WHERE id = :item_id
                """), {"item_id": item_id})
                
                row = result.fetchone()
                if not row:
                    flash('Item PM05 não encontrado', 'error')
                    return redirect(url_for('listar_pm05'))
                
                item = PM05Item(*row)
                
                # Buscar histórico
                hist_result = conn.execute(text("""
                    SELECT acao, detalhes, usuario, data_acao
                    FROM pm05_historico 
                    WHERE pm05_id = :item_id
                    ORDER BY data_acao DESC
                """), {"item_id": item_id})
                
                historico = [{'acao': h[0], 'detalhes': h[1], 'usuario': h[2], 'data': h[3]} 
                           for h in hist_result]
                
                # Calcular dias em reparo
                days_in_repair = 0
                if item.data_envio and item.status == 'EM_REPARO':
                    # Garantir que temos uma data, não uma string
                    if isinstance(item.data_envio, str):
                        data_envio = datetime.strptime(item.data_envio, '%Y-%m-%d').date()
                    elif hasattr(item.data_envio, 'date'):
                        data_envio = item.data_envio.date()
                    else:
                        data_envio = item.data_envio
                    
                    days_in_repair = (datetime.now().date() - data_envio).days
                
                # Calcular estatísticas específicas do item
                stats_result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as mesmo_fornecedor,
                        COALESCE(AVG(
                            CASE 
                                WHEN status = 'FINALIZADO' AND data_envio IS NOT NULL AND data_retorno IS NOT NULL
                                THEN julianday(data_retorno) - julianday(data_envio)
                                ELSE NULL
                            END
                        ), 0) as tempo_medio
                    FROM pm05_items 
                    WHERE fornecedor = :fornecedor AND id != :item_id
                """), {"fornecedor": item.fornecedor, "item_id": item_id})
                
                stats_row = stats_result.fetchone()
                stats = {
                    'mesmo_fornecedor': stats_row[0] if stats_row[0] else 0,
                    'tempo_medio': round(stats_row[1]) if stats_row[1] else 0
                }
                
                return render_template('detalhes_pm05.html', 
                                     item=item, 
                                     historico=historico,
                                     days_in_repair=days_in_repair,
                                     today_date=datetime.now().strftime('%Y-%m-%d'),
                                     stats=stats,
                                     format_date=format_date_safe,
                                     format_datetime=format_datetime_safe)
                
        except Exception as e:
            print(f"Erro ao carregar detalhes PM05: {e}")
            flash('Erro ao carregar detalhes', 'error')
            return redirect(url_for('listar_pm05'))
    
    @app.route('/pm05/editar/<int:id>')
    def editar_pm05(id):
        """Formulário para editar item PM05"""
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, numero_pm05, numero_invoice, descricao, catalog_envio, catalog_ersa,
                           quantidade, fornecedor, data_envio, data_retorno, spec, observacoes,
                           observacoes_retorno, nf_saida, nf_retorno, valor_reparo, status, data_criacao
                    FROM pm05_items WHERE id = :id
                """), {"id": id})
                
                row = result.fetchone()
                if not row:
                    flash('Item PM05 não encontrado', 'error')
                    return redirect(url_for('listar_pm05'))
                
                item = PM05Item(*row)
                
                # Calcular dias em reparo
                days_in_repair = 0
                if item.data_envio and item.status == 'EM_REPARO':
                    # Garantir que temos uma data, não uma string
                    if isinstance(item.data_envio, str):
                        data_envio = datetime.strptime(item.data_envio, '%Y-%m-%d').date()
                    elif hasattr(item.data_envio, 'date'):
                        data_envio = item.data_envio.date()
                    else:
                        data_envio = item.data_envio
                    
                    days_in_repair = (datetime.now().date() - data_envio).days
                
                return render_template('editar_pm05.html', 
                                     item=item,
                                     days_in_repair=days_in_repair,
                                     today_date=datetime.now().strftime('%Y-%m-%d'))
                
        except Exception as e:
            print(f"Erro ao carregar formulário de edição: {e}")
            flash('Erro ao carregar formulário', 'error')
            return redirect(url_for('listar_pm05'))
    
    @app.route('/pm05/atualizar/<int:id>', methods=['POST'])
    def atualizar_pm05(id):
        """Atualiza um item PM05"""
        try:
            with db.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE pm05_items SET
                        numero_pm05 = :numero_pm05,
                        numero_invoice = :numero_invoice,
                        descricao = :descricao,
                        catalog_envio = :catalog_envio,
                        catalog_ersa = :catalog_ersa,
                        quantidade = :quantidade,
                        fornecedor = :fornecedor,
                        data_envio = :data_envio,
                        spec = :spec,
                        observacoes = :observacoes,
                        nf_saida = :nf_saida,
                        valor_reparo = :valor_reparo,
                        status = :status
                    WHERE id = :id
                """), {
                    "id": id,
                    "numero_pm05": request.form.get('numero_pm05'),
                    "numero_invoice": request.form.get('numero_invoice'),
                    "descricao": request.form.get('descricao'),
                    "catalog_envio": request.form.get('catalog_envio'),
                    "catalog_ersa": request.form.get('catalog_ersa'),
                    "quantidade": int(request.form.get('quantidade')),
                    "fornecedor": request.form.get('fornecedor'),
                    "data_envio": request.form.get('data_envio'),
                    "spec": request.form.get('spec'),
                    "observacoes": request.form.get('observacoes'),
                    "nf_saida": request.form.get('nf_saida'),
                    "valor_reparo": float(request.form.get('valor_reparo')) if request.form.get('valor_reparo') else None,
                    "status": request.form.get('status', 'EM_REPARO')
                })
                conn.commit()
                
                flash('Item PM05 atualizado com sucesso!', 'success')
                return redirect(url_for('detalhes_pm05', id=id))
                
        except Exception as e:
            print(f"Erro ao atualizar PM05: {e}")
            flash('Erro ao atualizar item', 'error')
            return redirect(url_for('editar_pm05', id=id))
    
    @app.route('/pm05/deletar/<int:id>', methods=['POST'])
    def deletar_pm05(id):
        """Deleta um item PM05 - Para usuários logados ou admins"""
        
        # Verificar se o usuário está logado ou é admin
        if 'user_id' not in session and not session.get('is_admin', False):
            flash('Acesso negado. Faça login para deletar itens.', 'error')
            return redirect(url_for('listar_pm05'))
        
        try:
            with db.engine.connect() as conn:
                # Primeiro, buscar informações do item para o log
                result = conn.execute(text("""
                    SELECT numero_pm05, descricao, fornecedor 
                    FROM pm05_items WHERE id = :id
                """), {"id": id})
                
                row = result.fetchone()
                if not row:
                    flash('Item PM05 não encontrado', 'error')
                    return redirect(url_for('listar_pm05'))
                
                numero_pm05, descricao, fornecedor = row
                
                # Deletar anexos relacionados
                conn.execute(text("DELETE FROM pm05_anexos WHERE pm05_id = :id"), {"id": id})
                
                # Deletar histórico relacionado
                conn.execute(text("DELETE FROM pm05_historico WHERE pm05_id = :id"), {"id": id})
                
                # Deletar o item principal
                conn.execute(text("DELETE FROM pm05_items WHERE id = :id"), {"id": id})
                
                conn.commit()
                
                # Log da ação
                print(f"Item PM05 deletado: {numero_pm05} - {descricao} (Fornecedor: {fornecedor}) por usuário {session.get('username', 'Desconhecido')}")
                
                flash(f'Item PM05 {numero_pm05} deletado com sucesso!', 'success')
                return redirect(url_for('listar_pm05'))
                
        except Exception as e:
            print(f"Erro ao deletar PM05: {e}")
            flash('Erro ao deletar item PM05', 'error')
            return redirect(url_for('detalhes_pm05', item_id=id))
