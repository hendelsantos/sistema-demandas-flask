# Sistema de Controle de Demandas

Um sistema completo para gerenciamento de demandas de compra com controle de status, documentos e métricas financeiras.

## Funcionalidades

### 📋 Gestão de Demandas
- **Cadastro de Demandas**: Solicitante, descrição, quantidade, catálogo, local de uso e justificativa
- **Controle de Status**: 
  - Aberto → Em Cotação → PR Criada → PO Emitido
- **Upload de Documentos**: Anexar PDFs (cotações, especificações, POs, notas fiscais)
- **Timeline Visual**: Acompanhamento do fluxo do processo

### 🛒 Gestão de Pedidos
- **Criação de Pedidos**: Vinculados às demandas com PO emitido
- **Controle de Fornecedores**: Dados do fornecedor e número da PO
- **Gestão de Recebimento**: Confirmação de recebimento com valores reais
- **Notas Fiscais**: Controle de documentos fiscais

### 📊 Métricas e Relatórios
- **Previsões vs Recebido**: Comparativo mensal de valores
- **Gráficos Interativos**: Visualização de dados financeiros
- **Métricas em Tempo Real**: Dashboard com indicadores principais
- **Projeções Futuras**: Previsões de recebimento por mês

### 🎯 Dashboard
- **Visão Geral**: Totalizadores por status
- **Gráficos**: Status das demandas em pizza
- **Ações Rápidas**: Acesso direto às funcionalidades principais

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
