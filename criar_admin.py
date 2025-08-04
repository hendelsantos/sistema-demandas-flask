"""
Script para criar usuário admin padrão
Este script cria um usuário administrador padrão no sistema
"""
import os
import sys

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Usuario
from werkzeug.security import generate_password_hash

def criar_usuario_admin():
    """Cria usuário admin padrão"""
    print("🔧 CRIANDO USUÁRIO ADMIN PADRÃO")
    print("=" * 50)
    
    # Usar contexto da aplicação
    with app.app_context():
        try:
            # Verificar se já existe um admin
            admin_existente = Usuario.query.filter_by(username='admin').first()
            
            if admin_existente:
                print("⚠️ Usuário 'admin' já existe!")
                print(f"   Status admin: {admin_existente.is_admin}")
                
                # Perguntar se quer atualizar a senha
                resposta = input("💡 Deseja atualizar a senha do admin? (s/n): ")
                if resposta.lower() in ['s', 'sim', 'y', 'yes']:
                    admin_existente.set_password('admin123')
                    admin_existente.is_admin = True
                    db.session.commit()
                    print("✅ Senha do admin atualizada!")
                else:
                    print("ℹ️ Nenhuma alteração feita")
                return True
            
            # Criar novo usuário admin
            admin = Usuario(
                username='admin',
                is_admin=True
            )
            admin.set_password('admin123')
            
            # Adicionar ao banco
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuário admin criado com sucesso!")
            print("📋 Credenciais:")
            print("   👤 Usuário: admin")
            print("   🔑 Senha: admin123")
            print("   🔐 Permissões: Administrador")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar admin: {e}")
            db.session.rollback()
            return False

def listar_usuarios():
    """Lista todos os usuários do sistema"""
    print("\n📋 USUÁRIOS DO SISTEMA")
    print("=" * 50)
    
    with app.app_context():
        try:
            usuarios = Usuario.query.all()
            
            if not usuarios:
                print("📭 Nenhum usuário encontrado")
                return
            
            print(f"{'ID':<4} {'USUÁRIO':<15} {'ADMIN':<8} {'CRIADO EM':<20}")
            print("-" * 50)
            
            for user in usuarios:
                admin_status = "✅ Sim" if user.is_admin else "❌ Não"
                data_criacao = user.data_criacao.strftime('%d/%m/%Y %H:%M') if user.data_criacao else "N/A"
                print(f"{user.id:<4} {user.username:<15} {admin_status:<8} {data_criacao:<20}")
                
        except Exception as e:
            print(f"❌ Erro ao listar usuários: {e}")

def main():
    """Função principal"""
    print("👤 GERENCIADOR DE USUÁRIO ADMIN")
    print("=" * 50)
    
    # Verificar se as tabelas existem
    with app.app_context():
        try:
            # Criar tabelas se não existirem
            db.create_all()
            print("🗄️ Tabelas verificadas/criadas")
            
            # Criar usuário admin
            if criar_usuario_admin():
                # Listar usuários
                listar_usuarios()
                
                print("\n🎉 SETUP COMPLETO!")
                print("💡 Agora você pode fazer login com:")
                print("   👤 admin")
                print("   🔑 admin123")
            else:
                print("❌ Falha na criação do admin")
                
        except Exception as e:
            print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    main()
