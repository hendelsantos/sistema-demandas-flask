"""
Script de teste de conexão MySQL
Use este script para verificar se sua configuração MySQL está funcionando
"""
import pymysql

# Configurações do MySQL - EDITE AQUI!
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # COLOQUE SUA SENHA AQUI!
    'charset': 'utf8mb4'
}

def testar_conexao():
    """Testa conexão com MySQL"""
    print("🔍 Testando conexão MySQL...")
    print("=" * 40)
    
    # Verificar senha
    if not MYSQL_CONFIG['password']:
        print("❌ Configure a senha no script!")
        return False
    
    try:
        # Testar conexão
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # Testar query
        cursor.execute("SELECT VERSION()")
        versao = cursor.fetchone()
        
        print(f"✅ Conexão bem-sucedida!")
        print(f"📊 Versão MySQL: {versao[0]}")
        
        # Listar bancos
        cursor.execute("SHOW DATABASES")
        bancos = cursor.fetchall()
        print(f"🗃️ Bancos disponíveis:")
        for banco in bancos:
            print(f"   - {banco[0]}")
        
        # Verificar se banco sistema_demandas existe
        cursor.execute("SHOW DATABASES LIKE 'sistema_demandas'")
        banco_existe = cursor.fetchone()
        
        if banco_existe:
            print("✅ Banco 'sistema_demandas' encontrado!")
        else:
            print("⚠️ Banco 'sistema_demandas' não existe")
            print("   Será criado durante a migração")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 MySQL está pronto para migração!")
        return True
        
    except pymysql.err.OperationalError as e:
        error_code, error_msg = e.args
        print(f"❌ Erro de conexão: {error_msg}")
        
        if error_code == 1045:
            print("💡 Dica: Verifique usuário e senha")
        elif error_code == 2003:
            print("💡 Dica: Verifique se MySQL está rodando")
            print("   sudo systemctl start mysql")
        
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    """Função principal"""
    print("🧪 TESTE DE CONEXÃO MYSQL")
    print("=" * 50)
    
    sucesso = testar_conexao()
    
    if sucesso:
        print("\n✅ Tudo pronto! Execute: python migrar_sqlite_mysql.py")
    else:
        print("\n❌ Corrija os problemas antes de migrar")
    
    return sucesso

if __name__ == "__main__":
    main()
