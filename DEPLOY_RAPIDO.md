# 🚀 GUIA RÁPIDO - DEPLOY MYSQL

## ⚡ Start Rápido (5 minutos)

### 1. Preparar Ambiente
```bash
git clone https://github.com/hendelsantos/sistema-demandas-flask.git
cd sistema-demandas-flask
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Testar com SQLite (Desenvolvimento)
```bash
python criar_admin.py
python app.py
# Acesse: http://localhost:5000
# Login: admin / admin123
```

### 3. Migrar para MySQL (Produção)

#### A. Instalar MySQL
```bash
sudo apt update && sudo apt install mysql-server
sudo mysql_secure_installation
```

#### B. Configurar Banco
```sql
mysql -u root -p
CREATE DATABASE sistema_demandas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'senha123';
GRANT ALL PRIVILEGES ON sistema_demandas.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### C. Configurar Migração
Edite `migrar_sqlite_mysql.py`:
```python
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'app_user',        # ← CONFIGURE
    'password': 'senha123',    # ← CONFIGURE
    'database': 'sistema_demandas',
    'charset': 'utf8mb4'
}
```

#### D. Executar Migração
```bash
python testar_mysql.py      # Testar conexão
python migrar_sqlite_mysql.py  # Migrar dados
```

#### E. Ativar MySQL no App
Edite `app.py` linha 32:
```python
# Comentar SQLite:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demandas.db'

# Descomentar MySQL:
if os.getenv('MYSQL_HOST'):
    mysql_user = os.getenv('MYSQL_USER', 'app_user')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'senha123')
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_database = os.getenv('MYSQL_DATABASE', 'sistema_demandas')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demandas.db'
```

#### F. Criar .env
```bash
cat > .env << EOF
MYSQL_HOST=localhost
MYSQL_USER=app_user
MYSQL_PASSWORD=senha123
MYSQL_DATABASE=sistema_demandas
SECRET_KEY=sua-chave-secreta-aqui
EOF
```

### 4. Rodar com MySQL
```bash
python app.py
# Sistema rodando com MySQL! 🎉
```

## 🔧 Deploy Produção

### Nginx + Gunicorn
```bash
# Instalar Gunicorn
pip install gunicorn

# Rodar
gunicorn -w 4 -b 127.0.0.1:5000 app:app

# Nginx config
sudo nano /etc/nginx/sites-available/sistema-demandas
```

```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/sistema-demandas /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## 🆘 Problemas Comuns

### MySQL não conecta
```bash
sudo systemctl start mysql
python testar_mysql.py
```

### Erro de permissão
```bash
chmod 755 uploads/
chmod 664 instance/demandas.db
```

### Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 📱 Acesso ao Sistema

- **URL**: http://localhost:5000
- **Admin**: admin / admin123
- **Módulos**: Demandas, Pedidos, GI, PM05, Rede Social

## 🎯 Funcionalidades Principais

- ✅ Gestão de demandas e cotações
- ✅ Controle de pedidos e faturamento
- ✅ Indicadores GI com filtros anuais
- ✅ Rede social interna
- ✅ Dashboard com métricas
- ✅ Sistema de permissões
- ✅ Upload de arquivos
- ✅ Interface responsiva

---
**Sistema pronto para produção! 🚀**
