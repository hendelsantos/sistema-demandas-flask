"""
Módulo GI - Gestão de Indicadores
Sistema de comparativo entre valores realizados e pendentes por semana
"""
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from sqlalchemy import text

# Classe para representar dados do GI
class GI:
    def __init__(self, id=None, numero_semana=None, gi_realizado=None, gi_pendente=None, ano=None, data_criacao=None, data_atualizacao=None):
        self.id = id
        self.numero_semana = numero_semana
        self.gi_realizado = gi_realizado or 0
        self.gi_pendente = gi_pendente or 0
        self.ano = ano or datetime.now().year
        self.data_criacao = data_criacao
        self.data_atualizacao = data_atualizacao
    
    @property
    def total(self):
        return self.gi_realizado + self.gi_pendente
    
    @property
    def percentual_realizado(self):
        if self.total == 0:
            return 0
        return round((self.gi_realizado / self.total) * 100, 1)
    
    @property
    def percentual_pendente(self):
        if self.total == 0:
            return 0
        return round((self.gi_pendente / self.total) * 100, 1)

def criar_tabela_gi(db):
    """Cria a tabela do GI se não existir"""
    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gi_indicadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_semana INTEGER NOT NULL,
                gi_realizado DECIMAL(10,2) DEFAULT 0,
                gi_pendente DECIMAL(10,2) DEFAULT 0,
                ano INTEGER NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(numero_semana, ano)
            )
        """))
        conn.commit()

def obter_numero_semana_atual():
    """Retorna o número da semana atual"""
    hoje = datetime.now()
    return hoje.isocalendar()[1]

def obter_ano_atual():
    """Retorna o ano atual"""
    return datetime.now().year

def obter_dados_gi(db, ano=None):
    """Obtém todos os dados do GI para um ano específico"""
    if ano is None:
        ano = obter_ano_atual()
    
    with db.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, numero_semana, gi_realizado, gi_pendente, ano, 
                   data_criacao, data_atualizacao
            FROM gi_indicadores 
            WHERE ano = :ano
            ORDER BY numero_semana
        """), {"ano": ano})
        
        dados = []
        for row in result:
            gi = GI(
                id=row[0],
                numero_semana=row[1],
                gi_realizado=float(row[2]) if row[2] else 0,
                gi_pendente=float(row[3]) if row[3] else 0,
                ano=row[4],
                data_criacao=row[5],
                data_atualizacao=row[6]
            )
            dados.append(gi)
        
        return dados

def obter_estatisticas_gi(db, ano=None):
    """Obtém estatísticas gerais do GI"""
    if ano is None:
        ano = obter_ano_atual()
    
    with db.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_semanas,
                SUM(gi_realizado) as total_realizado,
                SUM(gi_pendente) as total_pendente,
                AVG(gi_realizado) as media_realizado,
                AVG(gi_pendente) as media_pendente
            FROM gi_indicadores 
            WHERE ano = :ano
        """), {"ano": ano})
        
        row = result.fetchone()
        if row:
            total_geral = (row[1] or 0) + (row[2] or 0)
            return {
                'total_semanas': row[0] or 0,
                'total_realizado': float(row[1]) if row[1] else 0,
                'total_pendente': float(row[2]) if row[2] else 0,
                'total_geral': total_geral,
                'media_realizado': float(row[3]) if row[3] else 0,
                'media_pendente': float(row[4]) if row[4] else 0,
                'percentual_realizado': round((float(row[1] or 0) / total_geral * 100), 1) if total_geral > 0 else 0,
                'percentual_pendente': round((float(row[2] or 0) / total_geral * 100), 1) if total_geral > 0 else 0
            }
        
        return {
            'total_semanas': 0,
            'total_realizado': 0,
            'total_pendente': 0,
            'total_geral': 0,
            'media_realizado': 0,
            'media_pendente': 0,
            'percentual_realizado': 0,
            'percentual_pendente': 0
        }

# Funções para as rotas (serão registradas no app principal)
def registrar_rotas_gi(app, db):
    """Registra todas as rotas do GI"""
    
    # Garantir que a tabela exista
    criar_tabela_gi(db)
    
    @app.route('/gi')
    def gi_dashboard():
        """Dashboard principal do GI"""
        try:
            # Obter ano da query string ou usar ano atual
            ano_solicitado = request.args.get('ano', type=int)
            ano_atual = obter_ano_atual()
            
            # Se não foi especificado ano ou ano inválido, usar ano atual
            if not ano_solicitado or ano_solicitado < 2020 or ano_solicitado > 2030:
                ano_solicitado = ano_atual
            
            semana_atual = obter_numero_semana_atual()
            
            # Obter dados do ano solicitado
            dados_gi = obter_dados_gi(db, ano_solicitado)
            
            # Obter estatísticas
            stats = obter_estatisticas_gi(db, ano_solicitado)
            
            # Verificar se existe registro para a semana atual (só se for o ano atual)
            registro_atual = None
            if ano_solicitado == ano_atual:
                for gi in dados_gi:
                    if gi.numero_semana == semana_atual:
                        registro_atual = gi
                        break
            
            return render_template('gi_dashboard.html',
                                 dados_gi=dados_gi,
                                 stats=stats,
                                 ano_atual=ano_solicitado,  # Ano que está sendo exibido
                                 ano_real=ano_atual,        # Ano real atual
                                 semana_atual=semana_atual,
                                 registro_atual=registro_atual)
            
        except Exception as e:
            print(f"Erro ao carregar GI dashboard: {e}")
            flash('Erro ao carregar dados do GI', 'error')
            ano_atual = obter_ano_atual()
            return render_template('gi_dashboard.html',
                                 dados_gi=[],
                                 stats={},
                                 ano_atual=ano_atual,
                                 ano_real=ano_atual,
                                 semana_atual=obter_numero_semana_atual(),
                                 registro_atual=None)
    
    @app.route('/gi/atualizar', methods=['POST'])
    def gi_atualizar():
        """Atualiza ou cria dados do GI para uma semana"""
        try:
            # Verificar se é admin
            if 'user_id' not in session:
                return jsonify({'error': 'Acesso negado. Faça login como administrador.'}), 403
            
            user_id = session['user_id']
            
            # Verificar se é admin usando SQL direto
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT is_admin FROM usuario WHERE id = :user_id"), {"user_id": user_id})
                user_row = result.fetchone()
                
                if not user_row or not user_row[0]:
                    return jsonify({'error': 'Acesso negado. Apenas administradores podem editar os dados.'}), 403
                
                # Obter dados do formulário
                numero_semana = request.form.get('numero_semana', type=int)
                gi_realizado = request.form.get('gi_realizado', type=float, default=0)
                gi_pendente = request.form.get('gi_pendente', type=float, default=0)
                ano = request.form.get('ano', type=int, default=obter_ano_atual())
                
                if not numero_semana or numero_semana < 1 or numero_semana > 53:
                    return jsonify({'error': 'Número da semana deve estar entre 1 e 53'}), 400
                
                # Verificar se já existe registro para esta semana e ano
                result = conn.execute(text("""
                    SELECT id FROM gi_indicadores 
                    WHERE numero_semana = :semana AND ano = :ano
                """), {"semana": numero_semana, "ano": ano})
                
                existing = result.fetchone()
                
                if existing:
                    # Atualizar registro existente
                    conn.execute(text("""
                        UPDATE gi_indicadores 
                        SET gi_realizado = :realizado, 
                            gi_pendente = :pendente,
                            data_atualizacao = CURRENT_TIMESTAMP
                        WHERE numero_semana = :semana AND ano = :ano
                    """), {
                        "realizado": gi_realizado,
                        "pendente": gi_pendente,
                        "semana": numero_semana,
                        "ano": ano
                    })
                else:
                    # Criar novo registro
                    conn.execute(text("""
                        INSERT INTO gi_indicadores (numero_semana, gi_realizado, gi_pendente, ano)
                        VALUES (:semana, :realizado, :pendente, :ano)
                    """), {
                        "semana": numero_semana,
                        "realizado": gi_realizado,
                        "pendente": gi_pendente,
                        "ano": ano
                    })
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Dados atualizados com sucesso!'})
                
        except Exception as e:
            print(f"Erro ao atualizar GI: {e}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.route('/gi/deletar/<int:gi_id>', methods=['POST'])
    def gi_deletar(gi_id):
        """Deleta um registro do GI - Apenas para admins"""
        try:
            # Verificar se é admin
            if 'user_id' not in session:
                return jsonify({'error': 'Acesso negado. Faça login como administrador.'}), 403
            
            user_id = session['user_id']
            
            with db.engine.connect() as conn:
                # Verificar se é admin
                result = conn.execute(text("SELECT is_admin FROM usuario WHERE id = :user_id"), {"user_id": user_id})
                user_row = result.fetchone()
                
                if not user_row or not user_row[0]:
                    return jsonify({'error': 'Acesso negado. Apenas administradores podem deletar registros.'}), 403
                
                # Deletar o registro
                result = conn.execute(text("""
                    DELETE FROM gi_indicadores WHERE id = :gi_id
                """), {"gi_id": gi_id})
                
                if result.rowcount == 0:
                    return jsonify({'error': 'Registro não encontrado'}), 404
                
                conn.commit()
                return redirect(url_for('gi_dashboard'))
                
        except Exception as e:
            print(f"Erro ao deletar GI: {e}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.route('/gi/semana-atual')
    def gi_semana_atual():
        """Retorna a semana atual via JSON para verificação automática"""
        return jsonify({
            'semana_atual': obter_numero_semana_atual(),
            'ano_atual': obter_ano_atual()
        })
