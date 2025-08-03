"""
Módulo da Rede Social - Sistema de Demandas
Mini rede social integrada ao sistema principal
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from sqlalchemy import text
import os
from datetime import datetime
import uuid

# Criar blueprint para a rede social
rede_social_bp = Blueprint('rede_social', __name__)

# Configurações de upload
UPLOAD_FOLDER_SOCIAL = 'static/uploads/social'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

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

from sqlalchemy import text

def criar_tabelas_rede_social(db):
    """Cria as tabelas necessárias para a rede social"""
    with db.engine.connect() as conn:
        # Tabela de posts
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS posts_social (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_autor VARCHAR(100) NOT NULL,
                conteudo TEXT NOT NULL,
                imagem VARCHAR(255),
                likes INTEGER DEFAULT 0,
                data_postagem TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Tabela de comentários
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comentarios_social (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                nome_autor VARCHAR(100) NOT NULL,
                conteudo TEXT NOT NULL,
                data_comentario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts_social (id)
            )
        """))
        
        # Tabela de curtidas
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS curtidas_social (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                ip_usuario VARCHAR(45) NOT NULL,
                data_curtida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(post_id, ip_usuario),
                FOREIGN KEY (post_id) REFERENCES posts_social (id)
            )
        """))
        
        conn.commit()

class Post:
    """Classe para representar um post"""
    def __init__(self, id, nome_autor, conteudo, imagem, likes, data_postagem):
        self.id = id
        self.nome_autor = nome_autor
        self.conteudo = conteudo
        self.imagem = imagem
        self.likes = likes
        self.data_postagem = data_postagem
        self.comentarios = []

class Comentario:
    """Classe para representar um comentário"""
    def __init__(self, id, post_id, nome_autor, conteudo, data_comentario):
        self.id = id
        self.post_id = post_id
        self.nome_autor = nome_autor
        self.conteudo = conteudo
        self.data_comentario = data_comentario

def obter_posts_com_comentarios(db):
    """Obtém todos os posts com seus comentários"""
    with db.engine.connect() as conn:
        # Buscar posts
        result = conn.execute(text("""
            SELECT id, nome_autor, conteudo, imagem, likes, data_postagem
            FROM posts_social
            ORDER BY data_postagem DESC
        """))
        
        posts = []
        for row in result:
            post = Post(
                id=row[0],
                nome_autor=row[1],
                conteudo=row[2],
                imagem=row[3],
                likes=row[4],
                data_postagem=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5]
            )
            
            # Buscar comentários do post
            comentarios_result = conn.execute(text("""
                SELECT id, post_id, nome_autor, conteudo, data_comentario
                FROM comentarios_social
                WHERE post_id = :post_id
                ORDER BY data_comentario ASC
            """), {"post_id": post.id})
            
            for com_row in comentarios_result:
                comentario = Comentario(
                    id=com_row[0],
                    post_id=com_row[1],
                    nome_autor=com_row[2],
                    conteudo=com_row[3],
                    data_comentario=datetime.fromisoformat(com_row[4]) if isinstance(com_row[4], str) else com_row[4]
                )
                post.comentarios.append(comentario)
            
            posts.append(post)
        
        return posts

def obter_estatisticas(db):
    """Obtém estatísticas da rede social"""
    with db.engine.connect() as conn:
        # Total de posts
        result = conn.execute(text("SELECT COUNT(*) FROM posts_social"))
        total_posts = result.fetchone()[0]
        
        # Total de comentários
        result = conn.execute(text("SELECT COUNT(*) FROM comentarios_social"))
        total_comentarios = result.fetchone()[0]
        
        # Total de curtidas
        result = conn.execute(text("SELECT SUM(likes) FROM posts_social"))
        total_likes = result.fetchone()[0] or 0
        
        # Usuários mais ativos
        result = conn.execute(text("""
            SELECT nome_autor, COUNT(*) as posts
            FROM posts_social
            GROUP BY nome_autor
            ORDER BY posts DESC
            LIMIT 5
        """))
        usuarios_ativos = [{'nome': row[0], 'posts': row[1]} for row in result]
        
        # Posts mais populares
        result = conn.execute(text("""
            SELECT conteudo, likes,
                   (SELECT COUNT(*) FROM comentarios_social WHERE post_id = posts_social.id) as comentarios
            FROM posts_social
            ORDER BY (likes + (SELECT COUNT(*) FROM comentarios_social WHERE post_id = posts_social.id)) DESC
            LIMIT 3
        """))
        posts_populares = []
        for row in result:
            posts_populares.append({
                'conteudo': row[0],
                'likes': row[1],
                'comentarios': [{'length': row[2]}]  # Simular structure para template
            })
        
        return {
            'total_posts': total_posts,
            'total_comentarios': total_comentarios,
            'total_likes': total_likes,
            'usuarios_ativos': usuarios_ativos,
            'posts_populares': posts_populares
        }

def criar_diretorio_uploads():
    """Cria o diretório de uploads se não existir"""
    if not os.path.exists(UPLOAD_FOLDER_SOCIAL):
        os.makedirs(UPLOAD_FOLDER_SOCIAL, exist_ok=True)

# Funções para as rotas (serão registradas no app principal)
def registrar_rotas_rede_social(app, db):
    """Registra todas as rotas da rede social"""
    
    # Garantir que as tabelas existam
    criar_tabelas_rede_social(db)
    criar_diretorio_uploads()
    
    # Importar Usuario dentro da função para evitar problemas de contexto
    from app import Usuario
    
    @app.route('/rede-social')
    def rede_social():
        """Página principal da rede social"""
        try:
            posts = obter_posts_com_comentarios(db)
            stats = obter_estatisticas(db)
            
            return render_template('rede_social.html',
                                 posts=posts,
                                 total_posts=stats['total_posts'],
                                 total_comentarios=stats['total_comentarios'],
                                 total_likes=stats['total_likes'],
                                 usuarios_ativos=stats['usuarios_ativos'],
                                 posts_populares=stats['posts_populares'])
        except Exception as e:
            print(f"Erro ao carregar rede social: {e}")
            return render_template('rede_social.html',
                                 posts=[],
                                 total_posts=0,
                                 total_comentarios=0,
                                 total_likes=0,
                                 usuarios_ativos=[],
                                 posts_populares=[])
    
    @app.route('/rede-social/postar', methods=['POST'])
    def postar():
        """Cria um novo post"""
        try:
            nome_autor = request.form.get('nome_autor', '').strip()
            conteudo = request.form.get('conteudo', '').strip()
            
            if not nome_autor or not conteudo:
                return jsonify({'error': 'Nome e conteúdo são obrigatórios'}), 400
            
            if len(conteudo) > 280:
                return jsonify({'error': 'Conteúdo muito longo (máximo 280 caracteres)'}), 400
            
            # Processar upload de imagem
            imagem_filename = None
            if 'imagem' in request.files:
                file = request.files['imagem']
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        file_size = get_file_size(file)
                        if file_size <= MAX_FILE_SIZE:
                            # Gerar nome único para o arquivo
                            filename = secure_filename(file.filename)
                            unique_filename = f"{uuid.uuid4()}_{filename}"
                            file_path = os.path.join(UPLOAD_FOLDER_SOCIAL, unique_filename)
                            file.save(file_path)
                            imagem_filename = unique_filename
                        else:
                            return jsonify({'error': 'Arquivo muito grande (máximo 5MB)'}), 400
                    else:
                        return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
            
            # Salvar no banco
            with db.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO posts_social (nome_autor, conteudo, imagem)
                    VALUES (:nome_autor, :conteudo, :imagem)
                """), {"nome_autor": nome_autor, "conteudo": conteudo, "imagem": imagem_filename})
                conn.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            print(f"Erro ao postar: {e}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.route('/rede-social/curtir/<int:post_id>', methods=['POST'])
    def curtir_post(post_id):
        """Curte ou descurte um post"""
        try:
            ip_usuario = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            with db.engine.connect() as conn:
                # Verificar se já curtiu
                result = conn.execute(text("""
                    SELECT id FROM curtidas_social 
                    WHERE post_id = :post_id AND ip_usuario = :ip_usuario
                """), {"post_id": post_id, "ip_usuario": ip_usuario})
                
                if result.fetchone():
                    # Descurtir
                    conn.execute(text("""
                        DELETE FROM curtidas_social 
                        WHERE post_id = :post_id AND ip_usuario = :ip_usuario
                    """), {"post_id": post_id, "ip_usuario": ip_usuario})
                    
                    conn.execute(text("""
                        UPDATE posts_social 
                        SET likes = likes - 1 
                        WHERE id = :post_id
                    """), {"post_id": post_id})
                else:
                    # Curtir
                    conn.execute(text("""
                        INSERT INTO curtidas_social (post_id, ip_usuario)
                        VALUES (:post_id, :ip_usuario)
                    """), {"post_id": post_id, "ip_usuario": ip_usuario})
                    
                    conn.execute(text("""
                        UPDATE posts_social 
                        SET likes = likes + 1 
                        WHERE id = :post_id
                    """), {"post_id": post_id})
                
                conn.commit()
                
                # Obter novo número de curtidas
                result = conn.execute(text("""
                    SELECT likes FROM posts_social WHERE id = :post_id
                """), {"post_id": post_id})
                
                likes = result.fetchone()[0]
                
                return jsonify({'likes': likes})
                
        except Exception as e:
            print(f"Erro ao curtir post: {e}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.route('/rede-social/comentar/<int:post_id>', methods=['POST'])
    def comentar_post(post_id):
        """Adiciona um comentário ao post"""
        try:
            nome_autor = request.form.get('nome_autor', '').strip()
            conteudo = request.form.get('conteudo', '').strip()
            
            if not nome_autor or not conteudo:
                return jsonify({'error': 'Nome e conteúdo são obrigatórios'}), 400
            
            if len(conteudo) > 500:
                return jsonify({'error': 'Comentário muito longo (máximo 500 caracteres)'}), 400
            
            with db.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO comentarios_social (post_id, nome_autor, conteudo)
                    VALUES (:post_id, :nome_autor, :conteudo)
                """), {"post_id": post_id, "nome_autor": nome_autor, "conteudo": conteudo})
                conn.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            print(f"Erro ao comentar: {e}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.route('/rede-social/deletar/<int:post_id>', methods=['POST'])
    def deletar_post(post_id):
        """Deleta um post - Apenas para admins"""
        try:
            print(f"DEBUG DELETE: Tentativa de deletar post {post_id}")
            
            # Verificar se o usuário é admin usando conexão direta ao banco
            from flask import session
            
            if 'user_id' not in session:
                print(f"DEBUG DELETE: Usuário não logado")
                return jsonify({'error': 'Acesso negado. Faça login para continuar.'}), 403
            
            user_id = session['user_id']
            print(f"DEBUG DELETE: user_id: {user_id}")
            
            # Verificar se é admin direto no banco
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT is_admin FROM usuario WHERE id = :user_id
                """), {"user_id": user_id})
                
                user_row = result.fetchone()
                if not user_row or not user_row[0]:
                    print(f"DEBUG DELETE: Acesso negado - não é admin ou usuário não encontrado")
                    return jsonify({'error': 'Acesso negado. Apenas administradores podem deletar posts.'}), 403
                
                print(f"DEBUG DELETE: Usuário é admin, prosseguindo com delete")
                
                # Buscar informações do post para deletar imagem se existir
                result = conn.execute(text("""
                    SELECT imagem FROM posts_social WHERE id = :post_id
                """), {"post_id": post_id})
                
                row = result.fetchone()
                if not row:
                    print(f"DEBUG DELETE: Post {post_id} não encontrado")
                    return jsonify({'error': 'Post não encontrado'}), 404
                
                imagem_filename = row[0]
                print(f"DEBUG DELETE: Post encontrado, imagem: {imagem_filename}")
                
                # Deletar comentários do post primeiro
                conn.execute(text("""
                    DELETE FROM comentarios_social WHERE post_id = :post_id
                """), {"post_id": post_id})
                
                # Deletar curtidas do post
                conn.execute(text("""
                    DELETE FROM curtidas_social WHERE post_id = :post_id
                """), {"post_id": post_id})
                
                # Deletar o post
                conn.execute(text("""
                    DELETE FROM posts_social WHERE id = :post_id
                """), {"post_id": post_id})
                
                conn.commit()
                print(f"DEBUG DELETE: Post {post_id} deletado do banco de dados")
                
                # Deletar arquivo de imagem se existir
                if imagem_filename:
                    try:
                        file_path = os.path.join(UPLOAD_FOLDER_SOCIAL, imagem_filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"DEBUG DELETE: Imagem {imagem_filename} deletada")
                        else:
                            print(f"DEBUG DELETE: Arquivo de imagem não existe: {file_path}")
                    except Exception as e:
                        print(f"Erro ao deletar imagem: {e}")
                
                print(f"DEBUG DELETE: Operação concluída com sucesso")
                return redirect(url_for('rede_social'))
                
        except Exception as e:
            print(f"Erro ao deletar post: {e}")
            import traceback
            print(f"DEBUG DELETE: Traceback completo: {traceback.format_exc()}")
            return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.route('/rede-social/editar/<int:post_id>', methods=['GET', 'POST'])
    def editar_post(post_id):
        """Edita um post - Apenas para admins"""
        try:
            # Verificar se o usuário é admin usando SQL direto para evitar problemas de contexto
            from flask import session
            if 'user_id' not in session:
                flash('Acesso negado. Faça login como administrador.', 'error')
                return redirect(url_for('rede_social'))
            
            user_id = session['user_id']
            
            # Verificar se é admin e processar a requisição usando a mesma conexão
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT is_admin FROM usuario WHERE id = :user_id"), {"user_id": user_id})
                user_row = result.fetchone()
                
                if not user_row or not user_row[0]:
                    flash('Acesso negado. Apenas administradores podem editar posts.', 'error')
                    return redirect(url_for('rede_social'))
                
                if request.method == 'GET':
                    # Buscar dados do post para edição
                    result = conn.execute(text("""
                        SELECT id, nome_autor, conteudo, imagem, likes, data_postagem
                        FROM posts_social WHERE id = :post_id
                    """), {"post_id": post_id})
                    
                    row = result.fetchone()
                    if not row:
                        flash('Post não encontrado', 'error')
                        return redirect(url_for('rede_social'))
                    
                    post = Post(
                        id=row[0],
                        nome_autor=row[1],
                        conteudo=row[2],
                        imagem=row[3],
                        likes=row[4],
                        data_postagem=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5]
                    )
                    
                    return render_template('editar_post.html', post=post)
                
                elif request.method == 'POST':
                    # Atualizar post
                    novo_conteudo = request.form.get('conteudo', '').strip()
                    
                    if not novo_conteudo:
                        return jsonify({'error': 'Conteúdo é obrigatório'}), 400
                    
                    if len(novo_conteudo) > 280:
                        return jsonify({'error': 'Conteúdo muito longo (máximo 280 caracteres)'}), 400
                    
                    # Atualizar no banco
                    conn.execute(text("""
                        UPDATE posts_social 
                        SET conteudo = :conteudo
                        WHERE id = :post_id
                    """), {"conteudo": novo_conteudo, "post_id": post_id})
                    
                    conn.commit()
                    
                    return jsonify({'success': True})
                
        except Exception as e:
            print(f"Erro ao editar post: {e}")
            if request.method == 'POST':
                return jsonify({'error': 'Erro interno do servidor'}), 500
            else:
                flash('Erro ao carregar post para edição', 'error')
                return redirect(url_for('rede_social'))
