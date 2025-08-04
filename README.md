# 🚀 Sistema de Demandas Flask

Sistema completo de gestão de demandas, pedidos e indicadores desenvolvido em Flask com interface moderna e responsiva.

## 📋 Visão Geral

Este sistema oferece uma solução completa para gestão empresarial com os seguintes módulos:

- 🎯 **Demandas**: Controle de solicitações e cotações
- 🛒 **Pedidos**: Gestão de pedidos e faturamento  
- 🌐 **Rede Social**: Posts e comunicação interna
- 📊 **PM05**: Indicadores de performance
- 📈 **GI**: Gestão de indicadores semanais
- 👥 **Usuários**: Sistema de autenticação e permissões

## ✨ Funcionalidades

### 🔐 Sistema de Autenticação
- Login/logout de usuários
- Controle de permissões (admin/usuário)
- Usuário admin padrão incluído

### 📊 Dashboard Interativo
- Cards de estatísticas
- Gráficos e métricas em tempo real
- Filtros por ano e período
- Interface responsiva

### 🎨 Interface Moderna
- Design Bootstrap 5
- PWA (Progressive Web App)
- Favicon personalizado
- Tema escuro/claro

### 📱 Recursos Técnicos
- SQLite/MySQL suportados
- Migrations automáticas
- Upload de arquivos
- API RESTful

## 🛠️ Tecnologias

- **Backend**: Flask 2.3.3, SQLAlchemy
- **Frontend**: Bootstrap 5, Font Awesome, JavaScript
- **Banco**: SQLite (padrão) / MySQL (produção)
- **Deploy**: Python 3.8+

## 📦 Instalação

### 1. Clone o Repositório
```bash
git clone https://github.com/hendelsantos/sistema-demandas-flask.git
cd sistema-demandas-flask
```

### 2. Ambiente Virtual
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

## 🚀 Execução Rápida (SQLite)

### 1. Inicializar Banco
```bash
# Criar usuário admin
python criar_admin.py

# Executar aplicação
python app.py
```

### 2. Acessar Sistema
- **URL**: http://localhost:5000
- **Admin**: admin / admin123
- **Público**: Alguns módulos acessíveis sem login

## 🐬 Configuração MySQL (Produção)

### 1. Instalar MySQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server

# Iniciar serviço
sudo systemctl start mysql
sudo systemctl enable mysql
```

### 2. Configurar Banco
```sql
# Conectar como root
mysql -u root -p

# Criar banco
CREATE DATABASE sistema_demandas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Criar usuário (opcional)
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'senha_segura';
GRANT ALL PRIVILEGES ON sistema_demandas.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Configurar Credenciais
Edite o arquivo `migrar_sqlite_mysql.py`:
```python
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',              # Seu usuário
    'password': 'sua_senha',     # Sua senha
    'database': 'sistema_demandas',
    'charset': 'utf8mb4'
}
```

### 4. Migração Automática
```bash
# Testar conexão
python testar_mysql.py

# Migrar dados do SQLite para MySQL
python migrar_sqlite_mysql.py
```

### 5. Ativar MySQL no App
Edite `app.py` e descomente as linhas MySQL:
```python
# Comentar SQLite
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demandas.db'

# Descomentar MySQL
if os.getenv('MYSQL_HOST'):
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_database = os.getenv('MYSQL_DATABASE', 'sistema_demandas')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
    print("🔗 Conectando ao MySQL...")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///demandas.db'
    print("🔗 Conectando ao SQLite...")
```

### 6. Configurar Variáveis de Ambiente
Crie o arquivo `.env`:
```env
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha
MYSQL_DATABASE=sistema_demandas

# Aplicação
SECRET_KEY=sua-chave-secreta-super-segura
FLASK_ENV=production
FLASK_DEBUG=False
```

### 7. Executar com MySQL
```bash
python app.py
```

## 🔧 Configuração de Servidor

### Nginx (Recomendado)
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Gunicorn (Produção)
```bash
# Instalar Gunicorn
pip install gunicorn

# Executar
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Systemd Service
```ini
[Unit]
Description=Sistema Demandas Flask
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/app
Environment="PATH=/path/to/app/venv/bin"
ExecStart=/path/to/app/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📊 Estrutura do Banco

### Tabelas Principais
- `demanda` - Demandas e cotações
- `pedido` - Pedidos e faturamento
- `usuario` - Usuários e permissões
- `post_rede_social` - Posts da rede social
- `pm05` - Indicadores PM05
- `gi_indicadores` - Indicadores GI semanais

### Relacionamentos
- Usuários têm permissões admin/user
- Demandas geram pedidos
- Posts pertencem a usuários
- Indicadores são filtrados por ano

## 🎯 Uso do Sistema

### 🔐 Login
1. Acesse http://localhost:5000/login
2. Use: admin / admin123
3. Ou crie novos usuários via admin

### 📊 Dashboard
- Visão geral de todos os módulos
- Estatísticas em tempo real
- Acesso rápido às funcionalidades

### Módulos Detalhados

#### 📋 Gestão de Demandas
- **Cadastro de Demandas**: Solicitante, descrição, quantidade, catálogo, local de uso e justificativa
- **Controle de Status**: 
  - Aberto → Em Cotação → PR Criada → PO Emitido
- **Upload de Documentos**: Anexar PDFs (cotações, especificações, POs, notas fiscais)
- **Timeline Visual**: Acompanhamento do fluxo do processo

#### 🛒 Gestão de Pedidos
- **Criação de Pedidos**: Vinculados às demandas com PO emitido
- **Controle de Fornecedores**: Dados do fornecedor e número da PO
- **Gestão de Recebimento**: Confirmação de recebimento com valores reais
- **Notas Fiscais**: Controle de documentos fiscais

#### 📊 Métricas e Relatórios
- **Previsões vs Recebido**: Comparativo mensal de valores
- **Gráficos Interativos**: Visualização de dados financeiros
- **Métricas em Tempo Real**: Dashboard com indicadores principais
- **Projeções Futuras**: Previsões de recebimento por mês

#### 📈 Indicadores GI
1. Inserir dados semanais
2. Filtrar por ano
3. Ver estatísticas
4. Editar/excluir registros

#### 🌐 Rede Social
1. Criar posts
2. Editar/excluir (admin)
3. Interação social
4. Comunicação interna

## 🔧 Desenvolvimento

### Estrutura de Arquivos
```
sistema-demandas-flask/
├── app.py                 # Aplicação principal
├── gi.py                  # Módulo GI
├── pm05.py               # Módulo PM05
├── rede_social.py        # Módulo Rede Social
├── criar_admin.py        # Script criar admin
├── migrar_sqlite_mysql.py # Script migração
├── requirements.txt      # Dependências
├── templates/            # Templates HTML
├── static/              # CSS, JS, imagens
├── instance/            # Banco SQLite
└── uploads/             # Arquivos enviados
```

### Comandos Úteis
```bash
# Instalar nova dependência
pip install nome-pacote
pip freeze > requirements.txt

# Backup banco
cp instance/demandas.db backup_$(date +%Y%m%d).db

# Ver logs
tail -f /var/log/nginx/access.log

# Reiniciar serviço
sudo systemctl restart nome-servico
```

## 🚨 Troubleshooting

### Erro de Conexão MySQL
```bash
# Verificar se MySQL está rodando
sudo systemctl status mysql

# Testar conexão
python testar_mysql.py

# Verificar logs
sudo tail -f /var/log/mysql/error.log
```

### Erro de Permissões
```bash
# Corrigir permissões uploads
chmod 755 uploads/
chown -R www-data:www-data uploads/

# Corrigir banco SQLite
chmod 664 instance/demandas.db
chown www-data:www-data instance/demandas.db
```

### Erro de Dependências
```bash
# Reinstalar dependências
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Limpar cache
pip cache purge
```

## 📞 Suporte

### Logs da Aplicação
- **SQLite**: Logs no terminal
- **MySQL**: /var/log/mysql/
- **Nginx**: /var/log/nginx/
- **App**: Configurar logging no Flask

### Contato
- **Desenvolvedor**: Hendel Santos
- **Email**: [seu-email@example.com]
- **GitHub**: https://github.com/hendelsantos/sistema-demandas-flask

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🏆 Versão

**Versão 1.02** - Sistema completo com todos os módulos funcionais

---

⭐ **Desenvolvido com ❤️ por Hendel Santos**
- **Gráficos Interativos**: Visualização de dados financeiros
- **Métricas em Tempo Real**: Dashboard com indicadores principais
- **Projeções Futuras**: Previsões de recebimento por mês

## Tecnologias Utilizadas

### Backend
- **Python 3.8+**
- **Flask** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **Flask-Migrate** - Migrações de banco
- **SQLite** - Banco de dados (desenvolvimento)

### Frontend
- **HTML5** e **CSS3**
- **Bootstrap 5** - Framework CSS
- **JavaScript ES6+**
- **Chart.js** - Gráficos interativos
- **Font Awesome** - Ícones

## Instalação e Configuração

### 1. Clonar o repositório
```bash
git clone <url-do-repositorio>
cd Sistema_demandas_flask
```

### 2. Criar ambiente virtual
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas configurações
nano .env
```

### 5. Inicializar banco de dados
```bash
# Criar migrações
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Executar aplicação
```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## Credenciais Padrão

O sistema cria automaticamente um usuário administrador para facilitar o primeiro acesso:

- **Usuário**: `admin`
- **Senha**: `admin123`

### Tipos de Usuário

#### 👨‍💼 Administrador
- Criar, editar e deletar demandas
- Atualizar status das demandas
- Gerenciar pedidos e recebimentos
- Visualizar todas as métricas
- Acesso completo ao sistema

#### 👤 Usuário Comum
- Criar novas demandas
- Visualizar demandas existentes
- Anexar documentos
- Visualizar métricas
- Acesso somente leitura para pedidos

> **Importante**: Após o primeiro acesso, é recomendado alterar a senha padrão do administrador e criar usuários específicos para cada pessoa da equipe.

## Estrutura do Projeto

```
Sistema_demandas_flask/
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências Python
├── .env.example          # Exemplo de configuração
├── README.md             # Este arquivo
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos personalizados
│   └── js/
│       └── script.js     # JavaScript personalizado
├── templates/            # Templates HTML
│   ├── base.html         # Template base
│   ├── index.html        # Página inicial
│   ├── dashboard.html    # Dashboard principal
│   ├── nova_demanda.html # Formulário de nova demanda
│   ├── listar_demandas.html # Lista de demandas
│   ├── detalhes_demanda.html # Detalhes da demanda
│   ├── listar_pedidos.html # Lista de pedidos
│   ├── novo_pedido.html  # Formulário de novo pedido
│   └── metricas.html     # Métricas e gráficos
├── uploads/              # Arquivos enviados (criado automaticamente)
└── migrations/           # Migrações do banco (criado automaticamente)
```

## Uso do Sistema

### 1. Criar Nova Demanda
1. Acesse "Nova Demanda" no menu
2. Preencha todos os campos obrigatórios
3. Salve a demanda (status inicial: "Aberto")

### 2. Gerenciar Status
1. Acesse os detalhes da demanda
2. Use o painel "Controle de Status" para atualizar
3. Acompanhe o progresso na timeline

### 3. Anexar Documentos
1. Na tela de detalhes da demanda
2. Selecione o tipo de documento
3. Faça upload do arquivo PDF
4. Documentos ficam organizados por tipo

### 4. Criar Pedido
1. Quando demanda estiver com "PO Emitido"
2. Clique em "Criar Pedido"
3. Preencha dados do fornecedor e valores
4. Defina previsão de recebimento

### 5. Confirmar Recebimento
1. Na lista de pedidos
2. Clique no botão de confirmação
3. Informe o valor real recebido
4. Sistema atualiza métricas automaticamente

### 6. Acompanhar Métricas
1. Acesse "Métricas" no menu
2. Visualize gráficos de previsão vs recebido
3. Acompanhe projeções futuras
4. Analise performance por mês

## Fluxo do Processo

```
1. DEMANDA CRIADA
   ↓ (Status: Aberto)
   
2. ENVIO PARA COTAÇÃO
   ↓ (Status: Em Cotação)
   
3. PR CRIADA
   ↓ (Status: PR Criada)
   
4. PO EMITIDO
   ↓ (Status: PO Emitido)
   
5. PEDIDO CRIADO
   ↓ (Vinculado à demanda)
   
6. RECEBIMENTO CONFIRMADO
   ↓ (Métricas atualizadas)
```

## Personalização

### Adicionar Novos Status
1. Edite o modelo `Demanda` em `app.py`
2. Atualize os templates HTML
3. Adicione validações necessárias

### Modificar Tipos de Arquivo
1. Altere a validação em `upload_arquivo()`
2. Atualize o frontend para novos tipos
3. Modifique as opções de seleção

### Customizar Métricas
1. Edite a rota `/api/metricas_chart`
2. Modifique queries SQL conforme necessário
3. Atualize gráficos no frontend

## Segurança

- ✅ Validação de uploads (apenas PDF)
- ✅ Sanitização de nomes de arquivo
- ✅ Controle de tamanho de arquivo
- ✅ Tokens CSRF nos formulários
- ✅ Validação de dados no backend

## Backup e Manutenção

### Backup do Banco
```bash
# SQLite
cp demandas.db backup_$(date +%Y%m%d).db
```

### Backup de Arquivos
```bash
# Pasta uploads
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

### Logs
- Logs são exibidos no console durante desenvolvimento
- Para produção, configure logging adequado

## Suporte e Desenvolvimento

### Requisitos do Sistema
- Python 3.8 ou superior
- 512MB RAM mínimo
- 1GB espaço em disco
- Navegador moderno (Chrome, Firefox, Safari, Edge)

### Contribuição
1. Fork o projeto
2. Crie branch para feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para branch (`git push origin feature/nova-funcionalidade`)
5. Abra Pull Request

## Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Contato

Para dúvidas ou sugestões, entre em contato através dos issues do repositório.
