"""
Script simplificado de migração de SQLite para MySQL
Este script migra todos os dados do banco SQLite atual para MySQL
"""
import sqlite3
import pymysql
from datetime import datetime
import os

# Configurações do MySQL - EDITE AQUI!
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # COLOQUE SUA SENHA AQUI!
    'database': 'sistema_demandas',
    'charset': 'utf8mb4'
}

def conectar_sqlite():
    """Conecta ao banco SQLite"""
    try:
        conn = sqlite3.connect('instance/demandas.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar SQLite: {e}")
        return None

def conectar_mysql():
    """Conecta ao banco MySQL"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar MySQL: {e}")
        print("💡 Verifique se:")
        print("   - MySQL está rodando")
        print("   - Credenciais estão corretas")
        print("   - Porta está acessível")
        return None

def criar_banco_mysql():
    """Cria o banco de dados MySQL se não existir"""
    try:
        config_sem_db = MYSQL_CONFIG.copy()
        database_name = config_sem_db.pop('database')
        
        conn = pymysql.connect(**config_sem_db)
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Banco '{database_name}' criado/verificado!")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao criar banco MySQL: {e}")
        return False

def criar_tabelas_mysql(mysql_conn):
    """Cria as tabelas no MySQL"""
    cursor = mysql_conn.cursor()
    
    tabelas = {
        'usuario': """
            CREATE TABLE IF NOT EXISTS usuario (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'demanda': """
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
        """,
        
        'arquivo_demanda': """
            CREATE TABLE IF NOT EXISTS arquivo_demanda (
                id INT AUTO_INCREMENT PRIMARY KEY,
                demanda_id INT NOT NULL,
                nome_arquivo VARCHAR(255) NOT NULL,
                nome_original VARCHAR(255) NOT NULL,
                tipo_arquivo VARCHAR(50) NOT NULL,
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (demanda_id) REFERENCES demanda(id) ON DELETE CASCADE
            )
        """,
        
        'pedido': """
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
        """,
        
        'posts_social': """
            CREATE TABLE IF NOT EXISTS posts_social (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome_autor VARCHAR(100) NOT NULL,
                conteudo TEXT NOT NULL,
                imagem VARCHAR(255),
                likes INT DEFAULT 0,
                data_postagem TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'comentarios_social': """
            CREATE TABLE IF NOT EXISTS comentarios_social (
                id INT AUTO_INCREMENT PRIMARY KEY,
                post_id INT NOT NULL,
                nome_autor VARCHAR(100) NOT NULL,
                conteudo TEXT NOT NULL,
                data_comentario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts_social(id) ON DELETE CASCADE
            )
        """,
        
        'pm05_processos': """
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
        """,
        
        'gi_indicadores': """
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
        """
    }
    
    for nome_tabela, sql in tabelas.items():
        try:
            cursor.execute(sql)
            print(f"  ✅ Tabela {nome_tabela} criada")
        except Exception as e:
            print(f"  ❌ Erro na tabela {nome_tabela}: {e}")
    
    mysql_conn.commit()
    print("📊 Estrutura de tabelas MySQL criada!")

def migrar_tabela(sqlite_conn, mysql_conn, tabela):
    """Migra dados de uma tabela do SQLite para MySQL"""
    try:
        # Verificar se tabela existe no SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabela}'")
        if not sqlite_cursor.fetchone():
            print(f"  ⚠️ Tabela {tabela} não encontrada no SQLite")
            return True
        
        # Obter dados do SQLite
        sqlite_cursor.execute(f"SELECT * FROM {tabela}")
        dados = sqlite_cursor.fetchall()
        
        if not dados:
            print(f"  📭 Tabela {tabela} está vazia")
            return True
        
        # Obter nomes das colunas
        colunas = [description[0] for description in sqlite_cursor.description]
        
        # Preparar inserção no MySQL
        mysql_cursor = mysql_conn.cursor()
        
        # Limpar tabela MySQL (opcional)
        mysql_cursor.execute(f"DELETE FROM {tabela}")
        
        # Construir query de inserção
        placeholders = ', '.join(['%s'] * len(colunas))
        colunas_str = ', '.join(colunas)
        query = f"INSERT INTO {tabela} ({colunas_str}) VALUES ({placeholders})"
        
        # Inserir dados
        registros_migrados = 0
        for linha in dados:
            try:
                # Converter tipos de dados se necessário
                valores = []
                for valor in linha:
                    if isinstance(valor, str) and valor in ('True', 'False'):
                        valores.append(valor == 'True')
                    else:
                        valores.append(valor)
                
                mysql_cursor.execute(query, valores)
                registros_migrados += 1
            except Exception as e:
                print(f"    ⚠️ Erro no registro: {e}")
        
        mysql_conn.commit()
        print(f"  ✅ {tabela}: {registros_migrados} registros migrados")
        return True
        
    except Exception as e:
        print(f"  ❌ Erro na migração de {tabela}: {e}")
        return False

def main():
    """Função principal de migração"""
    print("🔄 MIGRAÇÃO SQLite → MySQL")
    print("=" * 50)
    
    # Verificar configuração
    if not MYSQL_CONFIG['password']:
        print("❌ Configure a senha do MySQL no arquivo!")
        print("   Edite MYSQL_CONFIG['password'] no início do script")
        return False
    
    # Criar banco MySQL
    print("📦 Criando banco de dados MySQL...")
    if not criar_banco_mysql():
        return False
    
    # Conectar aos bancos
    print("🔗 Conectando aos bancos de dados...")
    sqlite_conn = conectar_sqlite()
    mysql_conn = conectar_mysql()
    
    if not sqlite_conn or not mysql_conn:
        print("❌ Falha nas conexões!")
        return False
    
    try:
        # Criar tabelas MySQL
        print("🏗️ Criando estrutura das tabelas...")
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
        print("📊 Migrando dados...")
        sucesso = True
        for tabela in tabelas:
            print(f"📋 Migrando: {tabela}")
            if not migrar_tabela(sqlite_conn, mysql_conn, tabela):
                sucesso = False
        
        if sucesso:
            print("\n" + "=" * 50)
            print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("📝 Próximos passos:")
            print("   1. Edite o arquivo .env com suas credenciais MySQL")
            print("   2. Reinicie a aplicação")
            print("   3. Teste todas as funcionalidades")
        else:
            print("\n⚠️ Migração concluída com alguns erros")
        
        return sucesso
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False
        
    finally:
        # Fechar conexões
        if sqlite_conn:
            sqlite_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("🔐 Conexões fechadas")

if __name__ == "__main__":
    main()
