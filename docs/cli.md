# 🛠️ CLI - Interface de Linha de Comando

O Crescent CLI é uma ferramenta poderosa para acelerar o desenvolvimento, gerando código automaticamente e gerenciando seu projeto.

---

## 📋 Comandos Disponíveis

```bash
luvit crescent-cli <comando> [opções]
```

### Comandos Principais

| Comando | Descrição |
|---------|-----------|
| `new <nome>` | Cria um novo projeto Crescent |
| `server` | Inicia o servidor de desenvolvimento |
| `test` | Executa todos os testes do projeto |
| `make:controller` | Gera um controller |
| `make:service` | Gera um service |
| `make:model` | Gera um model |
| `make:routes` | Gera arquivo de rotas |
| `make:module` | Gera módulo completo (CRUD) |
| `make:migration` | Cria uma migration |
| `migrate` | Executa migrations pendentes |
| `migrate:rollback` | Desfaz última migration |
| `migrate:status` | Mostra status das migrations |

---

## 🆕 Criar Novo Projeto

```bash
luvit crescent-cli new meu-projeto
```

**O que acontece:**
1. ✅ Clona o `crescent-starter` do GitHub
2. ✅ Remove histórico Git do template
3. ✅ Inicializa novo repositório Git
4. ✅ Configura estrutura completa

**Próximos passos após criação:**
```bash
cd meu-projeto
cp .env.example .env
nano .env  # Configure MySQL
luvit app.lua
```

---

## 🚀 Servidor de Desenvolvimento

```bash
luvit crescent-cli server
```

**Funcionalidades:**
- ✅ Inicia aplicação com `luvit app.lua`
- ✅ Logs em tempo real
- ✅ Substituição de processo (`exec`) para manter saída interativa
- ✅ Verifica se `app.lua` existe antes de iniciar

**Dica:** Para hot-reload automático, use `entr`:

```bash
find . -name "*.lua" | entr -r luvit crescent-cli server
```

---

## ✅ Executar Testes

```bash
luvit crescent-cli test
```

**Funcionalidades:**
- 🔍 Descobre automaticamente diretórios `tests/` ou `test/`
- 🔍 Encontra todos arquivos `*test*.lua` ou `*tests*.lua`
- ▶️ Executa cada teste sequencialmente
- 📊 Mostra saída completa de cada teste
- 📈 Apresenta resumo final com estatísticas
- ✅/❌ Feedback visual colorido com emojis

**Exemplo de saída (real, capturada rodando `runSuite` e o comando `test`):**
```
🌙 Executando Testes Crescent

ℹ Encontrados 1 arquivo(s) de teste

📄 Executando: tests/test-product.lua
────────────────────────────────────────────────────────────

=== Test Suite: Product Model Tests ===
Running test: testCreate
✅ testCreate passed
Running test: testUpdate
✅ testUpdate passed
Running test: testDelete
✅ testDelete passed

=== Results: 3/3 passed, 0 failed ===

════════════════════════════════════════════════════════════
🌙 Resumo dos Testes

Total de arquivos executados: 1

✅ Todos os testes passaram! (1/1)
```

> Cada suíte (`tests.runSuite`) sempre imprime `=== Test Suite: <nome> ===`
> e uma linha `Running test: <nome>` antes de cada resultado — é assim que
> `crescent/utils/tests.lua` funciona por baixo, independente de rodar via
> `luvit crescent-cli test` ou chamando o arquivo de teste direto.

---

## 🏗️ Geradores de Código

### Gerar Controller

```bash
luvit crescent-cli make:controller Product
# ou especificar módulo
luvit crescent-cli make:controller Product catalog
```

**Cria:** `src/product/controllers/product.lua`

**Template gerado:**
```lua
-- src/product/controllers/product.lua
-- Controller para Product

local service = require("src.product.services.product")
local ProductController = {}

function ProductController:index(ctx)
    local result = service:getAll()
    return ctx.json(200, result)
end

function ProductController:show(ctx)
    local id = ctx.params.id
    local result = service:getById(id)
    
    if result then
        return ctx.json(200, result)
    end
    return ctx.json(404, { error = "Not found" })
end

function ProductController:create(ctx)
    local body = ctx.body or {}
    local result = service:create(body)
    return ctx.json(201, result)
end

function ProductController:update(ctx)
    local id = ctx.params.id
    local body = ctx.body or {}
    local result = service:update(id, body)
    
    if result then
        return ctx.json(200, result)
    else
        return ctx.json(404, { error = "Not found" })
    end
end

function ProductController:delete(ctx)
    local id = ctx.params.id
    local success = service:delete(id)
    
    if success then
        return ctx.no_content()
    else
        return ctx.json(404, { error = "Not found" })
    end
end

return ProductController
```

---

### Gerar Service

```bash
luvit crescent-cli make:service Product
```

**Cria:** `src/product/services/product.lua`

**Template gerado:**
```lua
-- src/product/services/product.lua
-- Service para lógica de negócio de Product

local ProductService = {}
local Product = require("src.product.models.product")

function ProductService:getAll()
    return Product:all()
end

function ProductService:getById(id)
    return Product:find(id)
end

function ProductService:create(body)
   return Product:create(body)
end

function ProductService:update(id, body)
    local product = Product:find(id)
    if product then
        product:update(body)
        return product
    end
    return nil
end

function ProductService:delete(id)
    local product = Product:find(id)
    if product then
        product:delete()
        return true
    end
    return false
end

return ProductService
```

---

### Gerar Model

```bash
luvit crescent-cli make:model Product
```

**Cria:** `src/product/models/product.lua`

**Template gerado:**
```lua
-- src/product/models/product.lua
-- Model para Product usando Active Record ORM

local Model = require("crescent.database.model")

local Product = Model:extend({
    table = "product",
    primary_key = "id",
    timestamps = true,
    soft_deletes = false,
    
    fillable = {
        -- Adicione aqui os campos que podem ser preenchidos em massa
        "name",
    },
    
    hidden = {
        -- Campos que não devem aparecer em JSON/serialização
        -- "password"
    },

    guarded = {
        -- Campos protegidos contra mass assignment
        -- "id", "created_at", "updated_at"
    },
    
    validates = {
        -- Adicione validações aqui
        name = {required = true, min = 3, max = 255},
    },
    
    relations = {
        -- Defina relações aqui
        -- posts = {type = "hasMany", model = "Post", foreign_key = "user_id"},
        -- profile = {type = "hasOne", model = "Profile", foreign_key = "user_id"},
    }
})

-- Métodos personalizados do model
-- function Product:customMethod()
--     -- Seu código aqui
-- end

return Product
```

> ⚠️ O template gerado usa `validates = {min = 3, max = 255}` e
> `relations = { posts = {type = "hasMany", ...} }` como exemplo/lembrete
> nos comentários, mas essas chaves **não são reconhecidas** pela
> implementação real de `Model:validate()` (que só suporta `required`,
> `min_length`, `max_length`, `email`, `unique`) nem pelo mecanismo real de
> relações (que espera uma função, não uma tabela declarativa — veja
> **[Database & ORM → Relações](/docs/database#relações)**). Isso é um
> defeito do próprio gerador (`cli/templates.lua`), não só da doc — se for
> usar validação ou relações, troque pelo formato real documentado em
> [Database & ORM](/docs/database).

---

### Gerar Routes

```bash
luvit crescent-cli make:routes Product
```

**Cria:** `src/product/routes/product.lua`

**Template gerado:**
```lua
-- src/product/routes/product.lua
-- prefix definido em product/init.lua

local controller = require("src.product.controllers.product")

return function(app, prefix)
    prefix = prefix or "/product"
    
    -- CRUD completo
    app:get(prefix, function(ctx)
        return controller:index(ctx)
    end)
    
    app:get(prefix .. "/{id}", function(ctx)
        return controller:show(ctx)
    end)
    
    app:post(prefix, function(ctx)
        return controller:create(ctx)
    end)
    
    app:put(prefix .. "/{id}", function(ctx)
        return controller:update(ctx)
    end)
    
    app:delete(prefix .. "/{id}", function(ctx)
        return controller:delete(ctx)
    end)
end
```

---

### Gerar Módulo Completo

```bash
luvit crescent-cli make:module Product
```

**Cria tudo de uma vez:**
- ✅ Controller
- ✅ Service
- ✅ Model
- ✅ Routes
- ✅ Module Init

**Estrutura gerada:**
```
src/product/
├── init.lua
├── controllers/
│   └── product.lua
├── services/
│   └── product.lua
├── models/
│   └── product.lua
└── routes/
    └── product.lua
```

**Module Init (`src/product/init.lua`):**
```lua
-- src/product/init.lua
local Module = {}

function Module.register(app)
    local routes = require("src.product.routes.product")
    routes(app, "/product")
    
    print("✓ Módulo Product carregado")
end

return Module
```

**Registrar no app.lua:**
```lua
local ProductModule = require("src.product")
ProductModule.register(app)
```

---

## 🔄 Migrations

### Criar Migration

```bash
luvit crescent-cli make:migration create_products_table
```

**Padrões de nome reconhecidos:**

O nome da migration só decide qual **nome de tabela** é extraído — o SQL
gerado é sempre o mesmo (`CREATE TABLE IF NOT EXISTS <tabela> (...)` no
`up()`, `DROP TABLE IF EXISTS <tabela>` no `down()`), não importa qual dos
4 padrões você usa:

- `create_xxx_table` → tabela extraída: "xxx"
- `add_xxx_to_yyy` → tabela extraída: "yyy"
- `drop_xxx_table` → tabela extraída: "xxx"
- `update_xxx_table` → tabela extraída: "xxx"

Se o nome não bater com nenhum desses padrões, a tabela extraída é
`"example"`. O gerador **não** cria colunas específicas nem gera
`ALTER TABLE`/`ADD COLUMN` — sempre produz a mesma tabela genérica
(`id`, `name`, `created_at`, `updated_at`); editar `up()`/`down()` à mão
pra adicionar colunas/índices reais é o fluxo esperado (veja exemplos em
[Database & ORM → Migrations](/docs/database#migrations)).

**Cria:** `migrations/20260109123456_create_products_table.lua`

**Template gerado (sempre igual, independente do nome da migration):**
```lua
-- migrations/20260109123456_create_products_table.lua
-- Migration: create_products_table

local Migration = {}

-- Executa a migration (criar tabelas, adicionar colunas, etc)
function Migration:up()
    return [[
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    ]]
end

-- Desfaz a migration (remover tabelas, colunas, etc)
function Migration:down()
    return [[
        DROP TABLE IF EXISTS products;
    ]]
end

return Migration
```

---

### Executar Migrations

```bash
# Executar todas pendentes
luvit crescent-cli migrate

# Desfazer última migration
luvit crescent-cli migrate:rollback

# Ver status
luvit crescent-cli migrate:status
```

**Exemplo de saída (real, formato de `crescent/database/migrate.lua`):**
```
🌙 Executando Migrations

→ Executando: 20260108230701_create_users_table
  Executada com sucesso!
→ Executando: 20260109123456_create_products_table
  Executada com sucesso!

Total: 2 migration(s) executada(s)
```

---

## 🎯 Casos de Uso Comuns

### 1. Criar CRUD Completo

```bash
# 1. Criar migration
luvit crescent-cli make:migration create_categories_table

# 2. Editar migration (adicionar campos)
nano migrations/20260109_*.lua

# 3. Executar migration
luvit crescent-cli migrate

# 4. Criar módulo completo
luvit crescent-cli make:module Category

# 5. Registrar no app.lua
# Adicionar: CategoryModule.register(app)

# 6. Iniciar servidor
luvit crescent-cli server
```

### 2. Adicionar Funcionalidade a Módulo Existente

```bash
# Adicionar novo controller
luvit crescent-cli make:controller Admin users

# Adicionar novo service
luvit crescent-cli make:service Auth auth
```

### 3. Workflow de Testes

```bash
# Criar teste
touch tests/test-product.lua

# Implementar teste usando crescent/utils/tests
nano tests/test-product.lua

# Rodar testes
luvit crescent-cli test
```

---

## 🔧 Instalação Global do CLI

Para usar `crescent` sem `luvit crescent-cli`:

```bash
# No diretório do framework
./install.sh

# Agora use diretamente
crescent make:module Product
crescent server
crescent test
```

---

## 💡 Dicas Avançadas

### Aliases Bash

```bash
# Adicione no ~/.bashrc ou ~/.zshrc
alias cres='luvit crescent-cli'
alias cres-serve='luvit crescent-cli server'
alias cres-test='luvit crescent-cli test'

# Uso
cres make:module Product
cres-serve
cres-test
```

### Watch Mode com Entr

```bash
# Auto-restart no servidor
find . -name "*.lua" | entr -r luvit crescent-cli server

# Auto-run tests
find tests -name "*.lua" | entr -c luvit crescent-cli test
```

### Scripts Personalizados

Crie scripts no `package.lua` ou arquivos shell:

```bash
#!/bin/bash
# dev.sh - Script de desenvolvimento

echo "🔧 Instalando dependências..."
lit install

echo "🔄 Executando migrations..."
luvit crescent-cli migrate

echo "✅ Rodando testes..."
luvit crescent-cli test

echo "🚀 Iniciando servidor..."
luvit crescent-cli server
```

---

## 📖 Referência Rápida

```bash
# Criar projeto
crescent new app

# Geradores
crescent make:module User
crescent make:controller Product
crescent make:service Auth
crescent make:model Category
crescent make:routes Api

# Migrations
crescent make:migration create_posts_table
crescent migrate
crescent migrate:rollback
crescent migrate:status

# Desenvolvimento
crescent server
crescent test

# Help
crescent --help
```

---

## 🆘 Troubleshooting

### Erro: "crescent-cli.lua not found"

Execute o comando no diretório raiz do projeto onde está o arquivo `crescent-cli.lua`.

### Erro: "Permission denied"

```bash
chmod +x crescent-cli.lua
```

### CLI não cria arquivos

Verifique permissões de escrita no diretório:

```bash
ls -la src/
```

### Migration falha

1. Verifique sintaxe SQL no arquivo da migration
2. Confirme conexão com MySQL: `luvit crescent/database/mysql.lua`
3. Veja logs de erro completos

---

## 📚 Próximas Seções

- **[Core Concepts](/docs/core-concepts)** - Rotas, Controllers, Services
- **[Database & ORM](/docs/database)** - Migrations e Models em detalhes
- **[Utilities](/docs/utilities)** - Ferramentas de teste e helpers
