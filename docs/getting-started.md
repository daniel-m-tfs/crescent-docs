# 🚀 Começando

## O que é Crescent?

Crescent é um framework web completo que combina a performance do Lua/LuaJIT com uma arquitetura moderna e modular inspirada em frameworks como NestJS e Laravel. Foi projetado para criar APIs REST e aplicações web de alto desempenho com código limpo e organizado.

### 🌟 Principais Características

- **⚡ Performance**: Built on LuaJIT + libuv (Luvit) for blazing fast execution
- **🎯 Modular**: Organize código em módulos independentes e reutilizáveis
- **🗄️ ORM ActiveRecord**: Interaja com banco de dados MySQL de forma elegante
- **🔄 Migrations**: Sistema completo de versionamento de schema
- **🛠️ CLI Poderoso**: Geração automática de código (como Artisan do Laravel)
- **🔐 Segurança**: Middleware de segurança, validações e hash de senhas PBKDF2
- **✅ Testes**: Biblioteca completa de assertions para testes automatizados
- **📦 Pronto para Produção**: Configuração NGINX e systemd incluídas

---

## 📦 Instalação Rápida

### Método 1: Download Direto (Recomendado)

Baixe o template starter pronto para uso:


### Método 1: Via Lit Package Manager

```bash
# Instale o framework via Lit
lit install daniel-m-tfs/crescent-framework

# Clone o starter template
git clone https://github.com/daniel-m-tfs/crescent-starter.git meu-projeto
cd meu-projeto

# Configure e inicie
cp .env.example .env
nano .env
luvit app.lua
```

### Método 2: CLI (Criar Novo Projeto)

```bash
# Se você tem o CLI instalado globalmente
crescent new meu-projeto
cd meu-projeto
cp .env.example .env
nano .env
luvit app.lua
```

---

## 📚 Dependências

### Requisitos do Sistema

- **Luvit 2.18+**: Runtime Lua assíncrono
- **Lit 3.8+**: Gerenciador de pacotes
- **MySQL 5.7+** ou **MariaDB 10+**: Banco de dados
- **Linux/macOS**: Sistema operacional (Windows via WSL)

### Instalando Luvit e Lit

```bash
# macOS via Homebrew
brew install luvit

# Linux - Download manual
curl -L https://github.com/luvit/lit/raw/master/get-lit.sh | sh
```

### Dependências do Framework

O Crescent Framework automaticamente inclui:

- `luvit/luvit@2.18.1` - Runtime base
- `creationix/mysql` - Driver MySQL (instalar separadamente)

Para instalar o driver MySQL:

```bash
lit install creationix/mysql
```

---

## 📁 Estrutura do Projeto

```
crescent-starter/
├── app.lua                    # 🚀 Arquivo principal da aplicação
├── bootstrap.lua              # 🔧 Bootstrap do framework
├── crescent-cli.lua          # 🛠️ CLI para geração de código
├── .env                      # 🔐 Variáveis de ambiente (não versionar!)
├── .env.example              # 📝 Template de variáveis
├── config/
│   ├── development.lua       # ⚙️ Config de desenvolvimento
│   ├── production.lua        # ⚙️ Config de produção
│   ├── nginx.conf            # 🌐 Configuração NGINX
│   └── crescent.service      # 🔄 Systemd service
├── crescent/                 # 📦 Core do framework
│   ├── init.lua
│   ├── server.lua
│   ├── core/
│   │   ├── context.lua       # Contexto HTTP (req/res)
│   │   ├── request.lua       # Request object
│   │   ├── response.lua      # Response object
│   │   └── router.lua        # Sistema de rotas
│   ├── database/
│   │   ├── model.lua         # ORM ActiveRecord
│   │   ├── query_builder.lua # Query Builder
│   │   ├── mysql.lua         # Driver MySQL
│   │   └── migrate.lua       # Sistema de migrations
│   ├── middleware/
│   │   ├── auth.lua          # Autenticação
│   │   ├── cors.lua          # CORS
│   │   ├── logger.lua        # Logging
│   │   └── security.lua      # Segurança
│   └── utils/
│       ├── env.lua           # Variáveis de ambiente
│       ├── hash.lua          # 🔐 Hash de senhas PBKDF2
│       ├── tests.lua         # ✅ Biblioteca de testes
│       ├── headers.lua       # HTTP headers
│       ├── path.lua          # Path utilities
│       └── string.lua        # String utilities
├── src/                      # 📝 Seu código (módulos)
│   └── users/                # Exemplo de módulo
│       ├── init.lua          # Registrador do módulo
│       ├── controllers/
│       │   └── users.lua
│       ├── services/
│       │   └── users.lua
│       ├── models/
│       │   └── users.lua
│       └── routes/
│           └── users.lua
├── migrations/               # 🔄 Database migrations
│   └── 20260108230701_create_users_table.lua
└── tests/                    # ✅ Testes automatizados
    └── test-*.lua

```

### 🎯 Convenções de Diretórios

- **`src/`**: Todos os seus módulos de negócio
- **`crescent/`**: Core do framework (não modificar)
- **`config/`**: Arquivos de configuração
- **`migrations/`**: Versionamento do banco de dados
- **`tests/`**: Testes automatizados

---

## 🔧 Configuração Inicial

### 1. Variáveis de Ambiente (.env)

```bash
# Ambiente
ENV=development

# Banco de Dados
DB_HOST=localhost
DB_PORT=3306
DB_NAME=meu_banco
DB_USER=root
DB_PASSWORD=senha_segura

# Servidor
PORT=8080
HOST=0.0.0.0
```

### 2. Testar Conexão MySQL

```lua
-- teste-conexao.lua
local MySQL = require('crescent.database.mysql')

MySQL:test()
```

```bash
luvit teste-conexao.lua
```

### 3. Criar Primeira Migration

```bash
luvit crescent-cli make:migration create_products_table
```

### 4. Executar Migrations

```bash
luvit crescent-cli migrate
```

---

## 🎮 Primeiro Módulo

Crie um módulo CRUD completo com um único comando:

```bash
luvit crescent-cli make:module Product
```

Isso cria:
- ✅ Controller (`src/product/controllers/product.lua`)
- ✅ Service (`src/product/services/product.lua`)
- ✅ Model (`src/product/models/product.lua`)
- ✅ Routes (`src/product/routes/product.lua`)
- ✅ Module Init (`src/product/init.lua`)

### Registrar Módulo no app.lua

```lua
-- app.lua
local Crescent = require('crescent')
local app = Crescent.new()

-- Registra módulo Product
local ProductModule = require("src.product")
ProductModule.register(app)

-- app:listen(port, host) não recebe callback; "listening" já é
-- impresso pelo próprio framework
app:listen(8080)
```

---

## 🚀 Iniciando o Servidor

### Modo Desenvolvimento

```bash
luvit app.lua
```

Ou use o CLI:

```bash
luvit crescent-cli server
```

### Acessar API

```bash
# Listar produtos
curl http://localhost:8080/product

# Criar produto
curl -X POST http://localhost:8080/product \
  -H "Content-Type: application/json" \
  -d '{"name":"Notebook","price":2500}'

# Buscar por ID
curl http://localhost:8080/product/1

# Atualizar
curl -X PUT http://localhost:8080/product/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Notebook Dell","price":2800}'

# Deletar
curl -X DELETE http://localhost:8080/product/1
```

---

## 🧪 Executando Testes

```bash
# Rodar todos os testes
luvit crescent-cli test

# Rodar teste específico
luvit tests/test-users.lua
```

---

## 📖 Próximos Passos

Agora que você tem um projeto rodando, explore:

1. **[CLI](/docs/cli)** - Aprenda todos os comandos disponíveis
2. **[Core Concepts](/docs/core-concepts)** - Rotas, Controllers, Services
3. **[Database & ORM](/docs/database)** - Modelos, relações, migrations
4. **[Utilities](/docs/utilities)** - Testes, hash, helpers
5. **[Deployment](/docs/deployment)** - Deploy em produção

---

## 💡 Dicas Úteis

### Hot Reload (Desenvolvimento)

Use `nodemon` ou `entr` para reload automático:

```bash
# Com entr
find . -name "*.lua" | entr -r luvit app.lua
```

### Debug

```lua
-- Use p() para debug (pretty-print)
p(user)  -- Imprime tabela formatada
p(ctx.body)
```

### Performance

```lua
-- Use LuaJIT JIT compilation
-- Já habilitado por padrão no Luvit
```

---

## 🆘 Troubleshooting

### Erro: "Module not found"

```bash
# Instale dependências
lit install
```

### Erro: "MySQL connection failed"

1. Verifique se MySQL está rodando: `mysql.server status`
2. Teste credenciais: `mysql -u root -p`
3. Confira `.env`: `DB_HOST`, `DB_USER`, `DB_PASSWORD`

### Porta já em uso

```bash
# Mate processo na porta 8080
lsof -ti:8080 | xargs kill -9

# Ou mude a porta no .env
PORT=3000
```

---

## 📚 Recursos Adicionais

- [GitHub Repository](https://github.com/daniel-m-tfs/crescent-framework)
- [Starter Template](https://github.com/daniel-m-tfs/crescent-starter)
- [Luvit Documentation](https://luvit.io/)
- [Lit Package Manager](https://luvit.io/lit.html)
