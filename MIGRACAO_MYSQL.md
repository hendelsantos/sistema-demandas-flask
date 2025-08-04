# 🔄 MIGRAÇÃO PARA MYSQL

Este guia te ajudará a migrar seu sistema de SQLite para MySQL de forma segura e completa.

## 📋 PRÉ-REQUISITOS

### 1. MySQL instalado e rodando
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# Verificar se está rodando
sudo systemctl status mysql
```

### 2. Criar usuário e banco (opcional)
```sql
-- Conectar ao MySQL como root
mysql -u root -p

-- Criar banco de dados
CREATE DATABASE sistema_demandas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Criar usuário específico (opcional)
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'sua_senha_segura';
GRANT ALL PRIVILEGES ON sistema_demandas.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 🚀 PROCESSO DE MIGRAÇÃO

### Passo 1: Configurar credenciais
Edite o arquivo `migrar_sqlite_mysql.py` e configure suas credenciais MySQL:

```python
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',              # Seu usuário MySQL
    'password': 'SUA_SENHA',     # ⚠️ CONFIGURE AQUI!
    'database': 'sistema_demandas',
    'charset': 'utf8mb4'
}
```

### Passo 2: Executar migração
```bash
python migrar_sqlite_mysql.py
```

### Passo 3: Configurar aplicação
Edite o arquivo `.env` com suas credenciais:

```env
# Configuração do MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=SUA_SENHA
MYSQL_DATABASE=sistema_demandas

# Configuração da aplicação
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=development
```

### Passo 4: Testar aplicação
```bash
python app.py
```

## 📊 O QUE SERÁ MIGRADO

- ✅ **Usuários** - Todos os logins e permissões
- ✅ **Demandas** - Todas as demandas e histórico
- ✅ **Arquivos** - Referências aos arquivos
- ✅ **Pedidos** - Dados de PO e notas fiscais
- ✅ **Rede Social** - Posts e comentários
- ✅ **PM05** - Processos e cronogramas
- ✅ **GI** - Indicadores por semana/ano

## 🔒 SEGURANÇA

- ⚠️ **Backup**: Faça backup do banco SQLite antes da migração
- 🔐 **Credenciais**: Use senhas fortes para o MySQL
- 🗂️ **Arquivos**: Os arquivos em `/uploads` não são migrados automaticamente

## ❓ PROBLEMAS COMUNS

### Erro de conexão MySQL
```
❌ Erro ao conectar MySQL: (2003, "Can't connect to MySQL server")
```
**Solução**: Verifique se o MySQL está rodando e as credenciais estão corretas

### Erro de permissão
```
❌ Access denied for user 'root'@'localhost'
```
**Solução**: Verifique usuário e senha no MySQL

### Erro de charset
```
❌ Incorrect string value
```
**Solução**: O script já configura UTF8MB4, mas verifique se o MySQL suporta

## 🆘 ROLLBACK

Se algo der errado, você pode voltar ao SQLite:

1. Comente as linhas do MySQL no `app.py`
2. Descomente a linha do SQLite
3. Reinicie a aplicação

## ✅ VERIFICAÇÃO PÓS-MIGRAÇÃO

Após a migração, teste:

- [ ] Login funcionando
- [ ] Criação de demandas
- [ ] Upload de arquivos
- [ ] Rede social (posts/comentários)
- [ ] Módulo PM05
- [ ] Módulo GI
- [ ] Relatórios e estatísticas

---

## 📞 SUPORTE

Em caso de problemas:
1. Verifique os logs do MySQL
2. Confirme as credenciais no `.env`
3. Teste a conexão manual com o MySQL
