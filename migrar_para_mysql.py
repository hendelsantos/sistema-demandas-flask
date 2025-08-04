"""
Script de migração de SQLite para MySQL
Este script migra todos os dados do banco SQLite atual para MySQL
"""
import sqlite3
import pymysql
from datetime import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do MySQL
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'sistema_demandas'),
    'charset': 'utf8mb4'
}

def conectar_sqlite():
    """Conecta ao banco SQLite"""
    try:
        conn = sqlite3.connect('instance/demandas.db')
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        return conn
    except Exception as e:
        print(f"Erro ao conectar SQLite: {e}")
        return None

def conectar_mysql():
    """Conecta ao banco MySQL"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar MySQL: {e}")
        return None

def criar_banco_mysql():
    """Cria o banco de dados MySQL se não existir"""
    try:
        # Conectar sem especificar o database
        config_sem_db = MYSQL_CONFIG.copy()
        database_name = config_sem_db.pop('database')
        
        conn = pymysql.connect(**config_sem_db)
        cursor = conn.cursor()
        
        # Criar banco se não existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Banco de dados '{database_name}' criado/verificado com sucesso!")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao criar banco MySQL: {e}")
        return False

def criar_tabelas_mysql(mysql_conn):
    """Cria as tabelas no MySQL"""
    cursor = mysql_conn.cursor()
    
    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de demandas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demanda (
            id INT AUTO_INCREMENT PRIMARY KEY,
            solicitante VARCHAR(100) NOT NULL,
            descricao_item TEXT NOT NULL,
            quantidade INT NOT NULL,
            catalog VARCHAR(100),
            onde_utilizado VARCHAR(200) NOT NULL,
            justificativa TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'Aberto',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            ano_orcamentario INT,
            numero_demanda VARCHAR(20) UNIQUE,
            data_aberto TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_em_cotacao TIMESTAMP NULL,
            data_cotacao_aprovada TIMESTAMP NULL,
            data_po_emitido TIMESTAMP NULL,
            data_produto_recebido TIMESTAMP NULL,
            data_nf_recebida TIMESTAMP NULL
        )
    """)
    
    # Tabela de arquivos de demanda
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivo_demanda (
            id INT AUTO_INCREMENT PRIMARY KEY,
            demanda_id INT NOT NULL,
            nome_arquivo VARCHAR(255) NOT NULL,
            nome_original VARCHAR(255) NOT NULL,
            tipo_arquivo VARCHAR(50) NOT NULL,
            data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (demanda_id) REFERENCES demanda(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de pedidos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedido (
            id INT AUTO_INCREMENT PRIMARY KEY,
            demanda_id INT NOT NULL,
            numero_po VARCHAR(100),
            numero_nota_fiscal VARCHAR(100),
            valor_total DECIMAL(10,2),
            mes_previsto_recebimento VARCHAR(7),
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_recebimento TIMESTAMP NULL,
            data_recebimento_nf TIMESTAMP NULL,
            valor_recebido DECIMAL(10,2),
            fornecedor VARCHAR(200),
            FOREIGN KEY (demanda_id) REFERENCES demanda(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de posts da rede social
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts_social (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome_autor VARCHAR(100) NOT NULL,
            conteudo TEXT NOT NULL,
            imagem VARCHAR(255),
            likes INT DEFAULT 0,
            data_postagem TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de comentários da rede social
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comentarios_social (
            id INT AUTO_INCREMENT PRIMARY KEY,
            post_id INT NOT NULL,
            nome_autor VARCHAR(100) NOT NULL,
            conteudo TEXT NOT NULL,
            data_comentario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts_social(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de PM05
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pm05_processos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome_processo VARCHAR(200) NOT NULL,
            responsavel VARCHAR(100) NOT NULL,
            status VARCHAR(50) DEFAULT 'Em Andamento',
            data_inicio DATE NOT NULL,
            data_fim_prevista DATE NOT NULL,
            data_fim_real DATE,
            descricao TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de GI (Indicadores)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gi_indicadores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            numero_semana INT NOT NULL,
            gi_realizado DECIMAL(10,2) DEFAULT 0,
            gi_pendente DECIMAL(10,2) DEFAULT 0,
            ano INT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_semana_ano (numero_semana, ano)
        )
    """)
    
    mysql_conn.commit()
    print("Tabelas MySQL criadas com sucesso!")

def migrar_tabela(sqlite_conn, mysql_conn, tabela_sqlite, tabela_mysql=None):
    """Migra dados de uma tabela do SQLite para MySQL"""
    if tabela_mysql is None:
        tabela_mysql = tabela_sqlite
    
    try:
        # Obter dados do SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {tabela_sqlite}")
        dados = sqlite_cursor.fetchall()
        
        if not dados:
            print(f"Tabela {tabela_sqlite} está vazia ou não existe")
            return True
        
        # Obter nomes das colunas
        colunas = [description[0] for description in sqlite_cursor.description]
        
        # Preparar inserção no MySQL
        mysql_cursor = mysql_conn.cursor()
        
        # Construir query de inserção
        placeholders = ', '.join(['%s'] * len(colunas))
        colunas_str = ', '.join(colunas)
        query = f"INSERT INTO {tabela_mysql} ({colunas_str}) VALUES ({placeholders})"
        
        # Inserir dados
        for linha in dados:
            # Converter tipos de dados se necessário
            valores = []
            for valor in linha:
                if isinstance(valor, str) and valor in ('True', 'False'):
                    valores.append(valor == 'True')
                else:
                    valores.append(valor)
            
            mysql_cursor.execute(query, valores)
        
        mysql_conn.commit()
        print(f"Tabela {tabela_sqlite} migrada com sucesso! ({len(dados)} registros)")
        return True
        
    except Exception as e:
        print(f"Erro ao migrar tabela {tabela_sqlite}: {e}")
        return False

def main():
    """Função principal de migração"""
    print("🔄 Iniciando migração de SQLite para MySQL...")
    
    # Criar banco MySQL
    if not criar_banco_mysql():
        return False
    
    # Conectar aos bancos
    sqlite_conn = conectar_sqlite()
    mysql_conn = conectar_mysql()
    
    if not sqlite_conn or not mysql_conn:
        print("❌ Erro nas conexões!")
        return False
    
    try:
        # Criar tabelas MySQL
        criar_tabelas_mysql(mysql_conn)
        
        # Lista de tabelas para migrar
        tabelas = [
            'usuario',
            'demanda',
            'arquivo_demanda',
            'pedido',
            'posts_social',
            'comentarios_social',
            'pm05_processos',
            'gi_indicadores'
        ]
        
        # Migrar cada tabela
        for tabela in tabelas:
            print(f"📊 Migrando tabela: {tabela}")
            migrar_tabela(sqlite_conn, mysql_conn, tabela)
        
        print("✅ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False
        
    finally:
        # Fechar conexões
        if sqlite_conn:
            sqlite_conn.close()
        if mysql_conn:
            mysql_conn.close()

if __name__ == "__main__":
    main()
