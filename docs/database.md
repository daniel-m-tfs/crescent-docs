# 🗄️ Database & ORM

Sistema de ORM ActiveRecord, migrations e query builder.

---

## 🚀 Configuração do Banco

### .env

```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=meu_banco
DB_USER=root
DB_PASSWORD=senha123
```

### Testar Conexão

```lua
local MySQL = require('crescent.database.mysql')
MySQL.test()
```

---

## 💾 Models (ORM ActiveRecord)

### Definição Completa

```lua
-- src/products/models/product.lua
local Model = require("crescent.database.model")

local Product = Model:extend({
    -- Nome da tabela
    table = "products",

    -- Chave primária (padrão: "id")
    primary_key = "id",

    -- Timestamps automáticos (created_at, updated_at)
    timestamps = true,

    -- Soft delete: em vez de DELETE, escreve deleted_at e faz UPDATE
    soft_deletes = false,

    -- Campos que podem ser preenchidos em massa
    fillable = {
        "name",
        "description",
        "price",
        "stock",
        "category_id"
    },

    -- Campos escondidos em toArray()/toJSON() (não serializar)
    hidden = {
        "deleted_at"
    },

    -- Campos protegidos (nunca preenchidos em massa; tem prioridade sobre fillable)
    guarded = {
        "id",
        "created_at",
        "updated_at"
    },

    -- Validações (regras suportadas: required, min_length, max_length, email, unique)
    validates = {
        name = { required = true, min_length = 3, max_length = 255 },
        price = { required = true }
    },

    -- Relações: cada chave é uma função que recebe a instância e devolve
    -- o resultado de hasMany/hasOne/belongsTo (ver seção "Relações" abaixo)
    relations = {
        category = function(self)
            local Category = require("src.categories.models.category")
            return self:belongsTo(Category, "category_id")
        end
    },

    -- Hooks ficam direto na raiz da config (não dentro de um bloco "hooks")
    before_save = function(self)
        if self.name and not self.slug then
            self.slug = self.name:lower():gsub("%s+", "-")
        end
    end
})

-- Métodos personalizados
function Product:isLowStock()
    return self.stock < 10
end

function Product:applyDiscount(percentage)
    self.price = self.price * (1 - percentage / 100)
    self:save()
end

return Product
```

> `validates`, `relations` e os hooks (`before_create`, `after_create`, `before_save`,
> `after_save`, `before_update`, `after_update`, `before_delete`, `after_delete`) são
> todos opcionais.

---

## 📝 CRUD Operations

### CREATE

```lua
local Product = require('src.products.models.product')

-- Método 1: create() — valida, roda hooks, insere e devolve a instância
local product, errors = Product:create({
    name = "Notebook Dell",
    price = 2500,
    stock = 10
})

if not product then
    -- validação falhou (ou o insert falhou) — não lança erro, devolve nil + errors
    print(errors)
end

-- Método 2: new() + save()
local product = Product:new({
    name = "Mouse Logitech",
    price = 50
})
product:save()
```

### READ

```lua
-- Buscar por ID (devolve instância do Model ou nil)
local product = Product:find(1)

-- Buscar por ID ou lançar erro
local product = Product:findOrFail(1)

-- Todos os registros (array de instâncias do Model)
local products = Product:all()

-- Primeiro resultado (instância do Model)
local product = Product:first()

-- Com condições — where(coluna, operador, valor) ou where(coluna, valor) (operador = "=")
-- IMPORTANTE: Product:where(...) devolve um QueryBuilder, não instâncias do Model —
-- :get()/:first() aqui devolvem tabelas cruas do banco, sem os métodos do Model
local rows = Product:where("category_id", 5):get()
local row = Product:where("name", "Notebook"):first()

-- Ordenar, limitar (métodos do QueryBuilder — encadeiam depois de where()/query())
local products = Product:where("stock", ">", 0):orderBy("price", "DESC"):get()
local products = Product:query():limit(10):get()

-- Paginação manual (paginate só existe no QueryBuilder, não no Model)
local page, per_page = 1, 10
local products = Product:query():paginate(page, per_page):get()
```

### UPDATE

```lua
-- Método 1: Buscar e atualizar
local product = Product:find(1)
product:update({
    price = 2300,
    stock = 15
})

-- Método 2: Modificar e salvar
local product = Product:find(1)
product.price = 2300
product:save()

-- Método 3: Update direto via QueryBuilder (não roda hooks nem timestamps do Model)
Product:where("id", 1):update({price = 2300})
```

### DELETE

```lua
-- Se soft_deletes = true, isto grava deleted_at e faz UPDATE em vez de DELETE
local product = Product:find(1)
product:delete()

-- Delete direto por condição via QueryBuilder (ignora soft_deletes e hooks)
Product:where("stock", 0):delete()
```

---

## 🔍 Query Builder

Os métodos abaixo existem no `QueryBuilder` (`crescent/database/query_builder.lua`).
No `Model`, só `query()`, `find()`, `findOrFail()`, `first()`, `all()`, `where()` e
`raw()` existem como atalhos estáticos — para qualquer outro método (`join`,
`orderBy`, `limit`, `whereIn`, `paginate`, `count`, ...) comece a cadeia com
`Product:query()` ou `Product:where(...)`.

### Condições WHERE

```lua
-- Igualdade simples
Product:where("category_id", 5):get()

-- Operador explícito
Product:where("price", ">", 1000):get()
Product:where("stock", "<=", 5):get()

-- Múltiplas condições (AND, encadeando where)
Product:where("category_id", 5):where("stock", ">", 10):get()

-- WHERE IN
Product:query():whereIn("category_id", {1, 2, 3}):get()

-- WHERE NULL
Product:query():whereNull("deleted_at"):get()
Product:query():whereNotNull("discount"):get()
```

> Não existe `whereBetween`. Para isso, use duas condições
> (`:where("price", ">=", 1000):where("price", "<=", 5000)`) ou uma `raw()` query.

### OR Conditions

```lua
Product:where("category_id", 5)
       :orWhere("category_id", 10)
       :get()
```

### Ordenação

```lua
-- ASC (padrão)
Product:query():orderBy("name"):get()

-- DESC
Product:query():orderBy("price", "DESC"):get()

-- Múltiplas ordenações
Product:query()
       :orderBy("category_id")
       :orderBy("price", "DESC")
       :get()
```

> A direção é sempre normalizada para `ASC` ou `DESC` — qualquer outro valor vira `ASC`.

### Limit e Offset

```lua
-- LIMIT
Product:query():limit(10):get()

-- OFFSET
Product:query():offset(20):limit(10):get()

-- Paginação (limit/offset prontos; ainda precisa de :get())
Product:query():paginate(2, 20):get() -- página 2, 20 por página
```

> `paginate(page, per_page)` só ajusta `limit`/`offset` — não devolve total de
> registros nem número de páginas. Se precisar dessa metadata, calcule com uma
> query `:count()` separada (veja "Paginação" em Boas Práticas).

### Select

```lua
-- Selecionar campos específicos
Product:query():select("id", "name", "price"):get()

-- Com alias
Product:query():select("id", "name", "price as valor"):get()
```

### Joins

```lua
-- INNER JOIN (operador "=" é o padrão se omitido)
Product:query()
       :join("categories", "products.category_id", "categories.id")
       :select("products.*", "categories.name as category_name")
       :get()

-- LEFT JOIN
Product:query():leftJoin("categories", "products.category_id", "categories.id"):get()
```

### Agregações

```lua
-- COUNT
local total = Product:query():count()
local inStock = Product:where("stock", ">", 0):count()
```

> Só `count()` existe hoje — não há `sum`/`avg`/`min`/`max`/`groupBy`/`having`
> prontos no QueryBuilder. Para esses casos, use `raw()`.

### Raw Queries

```lua
-- SELECT raw (sempre use bindings com ? — nunca concatene valor de usuário na string)
local products = Product:raw([[
    SELECT * FROM products
    WHERE price > ? AND stock > ?
]], {1000, 0})

-- INSERT raw
Product:raw([[
    INSERT INTO products (name, price)
    VALUES (?, ?)
]], {"Teclado", 150})

-- Com bindings para segurança (evita SQL injection)
local search = ctx.query.search
local products = Product:raw([[
    SELECT * FROM products
    WHERE name LIKE ?
]], {"%" .. search .. "%"})
```

---

## ✅ Validações

### Validações Disponíveis

Só estas 5 regras existem em `Model:validate()` hoje:

```lua
validates = {
    -- Obrigatório
    name = { required = true },

    -- Tamanho mínimo/máximo de string
    name = { min_length = 3, max_length = 255 },

    -- Email (regex simples)
    email = { email = true },

    -- Único na tabela (ignora o próprio registro ao atualizar)
    email = { unique = true }
}
```

> Não há `numeric`, range numérico, `exists` (checagem de FK), `pattern`
> (regex customizado) ou `in_array` embutidos. Para essas validações, valide
> manualmente no Service (próxima seção) — é o padrão recomendado hoje.

### Validação no Service

```lua
-- src/products/services/products.lua
function ProductService:create(data)
    -- Validação customizada (o que o Model:validate() não cobre)
    if not data.price or data.price <= 0 then
        error("Invalid price")
    end

    if data.stock and data.stock < 0 then
        error("Stock cannot be negative")
    end

    -- Product:create() já roda as validações do Model (required/min_length/etc)
    local product, errors = Product:create(data)
    if not product then
        error(table.concat((function()
            local msgs = {}
            for _, msg in pairs(errors) do table.insert(msgs, msg) end
            return msgs
        end)(), ", "))
    end

    return product
end
```

---

## 🔗 Relações

Diferente de outros ORMs, relações no Crescent **não são declarativas** — cada
relação é uma função Lua que você chama explicitamente ou registra em
`relations` para carregar sob demanda via `instance:get("nome")`.

Três helpers de instância fazem o trabalho pesado:

| Método | Uso | Retorno |
|---|---|---|
| `self:belongsTo(RelatedModel, foreign_key, owner_key?)` | N:1 | instância do `RelatedModel` (ou `nil`) |
| `self:hasMany(RelatedModel, foreign_key, local_key?)` | 1:N | `QueryBuilder` (chame `:get()`) |
| `self:hasOne(RelatedModel, foreign_key, local_key?)` | 1:1 | linha crua da tabela (não é instância do Model) |

### Uso direto (sem configurar `relations`)

```lua
local Category = require("src.categories.models.category")
local Product = require("src.products.models.product")

local product = Product:find(1)
local category = product:belongsTo(Category, "category_id")
print(category.name)

local category2 = Category:find(1)
local products = category2:hasMany(Product, "category_id"):get()
for _, row in ipairs(products) do
    print(row.name)
end
```

### Registrando em `relations` (carregamento preguiçoso e cacheado)

```lua
local Product = Model:extend({
    table = "products",
    relations = {
        category = function(self)
            local Category = require("src.categories.models.category")
            return self:belongsTo(Category, "category_id")
        end
    }
})

local product = Product:find(1)
local category = product:get("category") -- NÃO product:category() nem product.category
```

> `instance:get("category")` chama a função uma única vez e guarda o
> resultado em cache na própria instância; chamadas seguintes reaproveitam o
> valor.

> Não há `belongsToMany` (N:N com tabela pivot) nem eager loading (`:with(...)`)
> hoje. Relações N:N precisam ser resolvidas manualmente com `raw()` ou um
> `join()`. Para evitar N+1 em listagens, veja "N+1 Problem" em Boas Práticas.

---

## 🔄 Migrations

### Criar Migration

```bash
luvit crescent-cli make:migration create_products_table
```

Isso gera um arquivo em `migrations/` com uma tabela mínima (`id`, `name`,
`created_at`, `updated_at`) — edite o SQL gerado para o schema real.

### Migration de Criação

```lua
-- migrations/20260109123456_create_products_table.lua
local Migration = {}

function Migration:up()
    return [[
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            stock INT DEFAULT 0,
            category_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            INDEX idx_category (category_id),
            INDEX idx_price (price),

            FOREIGN KEY (category_id)
                REFERENCES categories(id)
                ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    ]]
end

function Migration:down()
    return [[
        DROP TABLE IF EXISTS products;
    ]]
end

return Migration
```

> Cada migration roda com uma única chamada `MySQL:query(sql)` por cima do
> driver — evite depender de múltiplas instruções separadas por `;` num só
> `up()`/`down()` funcionando como transação; prefira uma instrução DDL por
> migration quando possível.

### Executar Migrations

```bash
# Executar pendentes
luvit crescent-cli migrate

# Desfazer última
luvit crescent-cli migrate:rollback

# Status
luvit crescent-cli migrate:status
```

---

## 🪝 Hooks (Lifecycle Events)

Os hooks ficam **direto na raiz** da config passada para `Model:extend()` —
não existe um bloco `hooks = {...}` agrupando eles.

```lua
local Product = Model:extend({
    table = "products",

    before_save = function(self)
        -- Antes de salvar (CREATE ou UPDATE)
        print("Saving product:", self.name)
    end,

    after_save = function(self)
        -- Depois de salvar
        print("Product saved:", self.id)
    end,

    before_create = function(self)
        -- Antes de criar
        self.slug = self.name:lower():gsub("%s+", "-")
    end,

    after_create = function(self)
        -- Depois de criar
        print("New product created!")
    end,

    before_update = function(self) end,
    after_update = function(self) end,

    before_delete = function(self)
        -- Antes de deletar (soft ou hard)
        local orderCount = OrderItem:where("product_id", self.id):count()
        if orderCount > 0 then
            error("Cannot delete product with existing orders")
        end
    end,

    after_delete = function(self) end
})
```

---

## 💡 Boas Práticas

### Índices

```sql
-- Campos frequentemente buscados
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_status ON orders(status);

-- Chaves estrangeiras
CREATE INDEX idx_category_id ON products(category_id);

-- Compostos para queries complexas
CREATE INDEX idx_category_price ON products(category_id, price);
```

### Transações

O `mysql.lua` atual pega uma conexão do pool por chamada e a devolve ao fim
dela — chamadas separadas (`db:query("START TRANSACTION")`, depois outras
queries, depois `db:query("COMMIT")`) **não têm garantia de rodar na mesma
conexão**, então isso não funciona como uma transação atômica de verdade.
Não há suporte a transações no ORM hoje; trate isso como uma limitação
conhecida (e evite depender de rollback automático) até que o driver exponha
uma conexão dedicada por transação.

### N+1 Problem

```lua
-- ❌ Ruim (N+1 queries: 1 pra listar produtos + 1 por produto)
local products = Product:all()
for _, product in ipairs(products) do
    local category = product:belongsTo(Category, "category_id")
end

-- ✅ Melhor: uma query pros produtos + uma query batelada pras categorias
local products = Product:all()
local category_ids = {}
for _, product in ipairs(products) do
    table.insert(category_ids, product.category_id)
end

local categories_by_id = {}
for _, row in ipairs(Category:query():whereIn("id", category_ids):get()) do
    categories_by_id[row.id] = row
end

for _, product in ipairs(products) do
    local category = categories_by_id[product.category_id]
end
```

> Não há eager loading (`:with(...)`) embutido — o padrão acima (buscar IDs e
> fazer um `whereIn` batelado) é a forma recomendada de evitar N+1 hoje.

### Paginação

`paginate()` só ajusta `limit`/`offset`; total de registros e número de
páginas precisam ser calculados à parte:

```lua
-- No controller
function ProductController:index(ctx)
    local page = tonumber(ctx.query.page) or 1
    local per_page = tonumber(ctx.query.per_page) or 20

    local total = Product:query():count()
    local data = Product:query():paginate(page, per_page):get()

    return ctx.json(200, {
        data = data,
        current_page = page,
        per_page = per_page,
        total = total,
        last_page = math.ceil(total / per_page)
    })
end
```

---

## 🧪 Testando Database

```lua
-- tests/test-product.lua
local tests = require('crescent.utils.tests')
local Product = require('src.products.models.product')

local productTests = {
    testCreate = function()
        local product = Product:create({
            name = "Test Product",
            price = 100,
            stock = 10
        })

        tests.assertNotNil(product)
        tests.assertNotNil(product.id)
        tests.assertEquals(product.name, "Test Product")
    end,

    testValidation = function()
        -- Product:create() não lança erro em falha de validação —
        -- devolve nil + uma tabela de erros
        local product, errors = Product:create({name = ""})
        tests.assertNil(product)
        tests.assertNotNil(errors)
    end,

    testRelations = function()
        local Category = require('src.categories.models.category')
        local product = Product:find(1)
        local category = product:belongsTo(Category, "category_id")

        tests.assertNotNil(category)
        tests.assertIsTable(category)
    end
}

tests.runSuite("Product Model Tests", productTests)
```

---

## 📖 Próximas Seções

- **[Core Concepts](/docs/core-concepts)** - Controllers e Services
- **[Utilities](/docs/utilities)** - Testes e helpers
- **[Deployment](/docs/deployment)** - Deploy em produção
