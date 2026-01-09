# 🗄️ Database & ORM

Sistema completo de ORM ActiveRecord, migrations e query builder.

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
MySQL:test()
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
    
    -- Soft deletes (deleted_at)
    soft_deletes = false,
    
    -- Campos que podem ser preenchidos em massa
    fillable = {
        "name",
        "description",
        "price",
        "stock",
        "category_id"
    },
    
    -- Campos escondidos em JSON (não serializar)
    hidden = {
        "deleted_at"
    },
    
    -- Campos protegidos (nunca preenchidos em massa)
    guarded = {
        "id",
        "created_at",
        "updated_at"
    },
    
    -- Validações
    validates = {
        name = {
            required = true,
            min = 3,
            max = 255,
            unique = true
        },
        price = {
            required = true,
            numeric = true,
            min = 0
        },
        stock = {
            numeric = true,
            min = 0
        },
        category_id = {
            exists = {table = "categories", column = "id"}
        }
    },
    
    -- Relações
    relations = {
        category = {
            type = "belongsTo",
            model = "Category",
            foreign_key = "category_id"
        },
        orders = {
            type = "hasMany",
            model = "OrderItem",
            foreign_key = "product_id"
        }
    }
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

---

## 📝 CRUD Operations

### CREATE

```lua
local Product = require('src.products.models.product')

-- Método 1: create()
local product = Product:create({
    name = "Notebook Dell",
    price = 2500,
    stock = 10
})

-- Método 2: new() + save()
local product = Product:new({
    name = "Mouse Logitech",
    price = 50
})
product:save()
```

### READ

```lua
-- Buscar por ID
local product = Product:find(1)

-- Todos os registros
local products = Product:all()

-- Com condições
local products = Product:where({category_id = 5}):get()

-- Primeiro resultado
local product = Product:where({name = "Notebook"}):first()

-- Ordenar
local products = Product:orderBy('price', 'DESC'):get()

-- Limitar
local products = Product:limit(10):get()

-- Paginação
local products = Product:paginate(10, 1)  -- 10 por página, página 1
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

-- Método 3: Update direto
Product:where({id = 1}):update({price = 2300})
```

### DELETE

```lua
-- Soft delete (se soft_deletes = true)
local product = Product:find(1)
product:delete()

-- Hard delete (força remoção permanente)
product:forceDelete()

-- Delete direto por condição
Product:where({stock = 0}):delete()
```

---

## 🔍 Query Builder

### Condições WHERE

```lua
-- Igualdade simples
Product:where({category_id = 5}):get()

-- Múltiplas condições (AND)
Product:where({
    category_id = 5,
    stock = {">", 10}
}):get()

-- Operadores
Product:where({price = {">", 1000}}):get()
Product:where({stock = {"<=", 5}}):get()
Product:where({name = {"LIKE", "%Dell%"}}):get()

-- WHERE IN
Product:whereIn('category_id', {1, 2, 3}):get()

-- WHERE BETWEEN
Product:whereBetween('price', 1000, 5000):get()

-- WHERE NULL
Product:whereNull('deleted_at'):get()
Product:whereNotNull('discount'):get()
```

### OR Conditions

```lua
Product:where({category_id = 5})
       :orWhere({category_id = 10})
       :get()
```

### Ordenação

```lua
-- ASC
Product:orderBy('name'):get()
Product:orderBy('name', 'ASC'):get()

-- DESC
Product:orderBy('price', 'DESC'):get()

-- Múltiplas ordenações
Product:orderBy('category_id')
       :orderBy('price', 'DESC')
       :get()
```

### Limit e Offset

```lua
-- LIMIT
Product:limit(10):get()

-- OFFSET
Product:offset(20):limit(10):get()

-- Paginação
Product:paginate(20, 2)  -- 20 por página, página 2
```

### Select

```lua
-- Selecionar campos específicos
Product:select('id', 'name', 'price'):get()

-- Com alias
Product:select('id', 'name', 'price as valor'):get()
```

### Joins

```lua
-- INNER JOIN
Product:join('categories', 'products.category_id', 'categories.id')
       :select('products.*', 'categories.name as category_name')
       :get()

-- LEFT JOIN
Product:leftJoin('categories', 'products.category_id', 'categories.id'):get()
```

### Agrupamento

```lua
-- GROUP BY
Product:select('category_id', 'COUNT(*) as total')
       :groupBy('category_id')
       :get()

-- HAVING
Product:select('category_id', 'AVG(price) as avg_price')
       :groupBy('category_id')
       :having('avg_price', '>', 1000)
       :get()
```

### Agregações

```lua
-- COUNT
local total = Product:count()
local inStock = Product:where({stock = {">", 0}}):count()

-- SUM
local totalValue = Product:sum('price')

-- AVG
local avgPrice = Product:avg('price')

-- MIN / MAX
local minPrice = Product:min('price')
local maxPrice = Product:max('price')
```

### Raw Queries

```lua
-- SELECT raw
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

```lua
validates = {
    -- Obrigatório
    name = { required = true },
    
    -- Tamanho string
    name = { min = 3, max = 255 },
    
    -- Numérico
    price = { numeric = true },
    
    -- Range numérico
    stock = { min = 0, max = 9999 },
    
    -- Email
    email = { email = true },
    
    -- Único na tabela
    email = { unique = true },
    
    -- Existe em outra tabela
    category_id = {
        exists = {
            table = "categories",
            column = "id"
        }
    },
    
    -- Regex customizado
    phone = { pattern = "^%d%d%d%-%d%d%d%d$" },
    
    -- Valores permitidos
    status = { in_array = {"pending", "paid", "shipped"} }
}
```

### Validação Manual

```lua
-- No Model
function Product:validate()
    local errors = {}
    
    if not self.name or #self.name < 3 then
        table.insert(errors, "Name must be at least 3 characters")
    end
    
    if self.price and self.price < 0 then
        table.insert(errors, "Price cannot be negative")
    end
    
    if #errors > 0 then
        error(table.concat(errors, ", "))
    end
    
    return true
end
```

### Validação no Service

```lua
-- src/products/services/products.lua
function ProductService:create(data)
    -- Validação customizada
    if not data.price or data.price <= 0 then
        error("Invalid price")
    end
    
    if data.stock and data.stock < 0 then
        error("Stock cannot be negative")
    end
    
    -- ORM faz validações do Model automaticamente
    return Product:create(data)
end
```

---

## 🔗 Relações

### BelongsTo (N:1)

```lua
-- Product pertence a Category
local Product = Model:extend({
    table = "products",
    
    relations = {
        category = {
            type = "belongsTo",
            model = "Category",
            foreign_key = "category_id"
        }
    }
})

-- Uso
local product = Product:find(1)
local category = product:category()  -- Busca a categoria

print(category.name)
```

### HasMany (1:N)

```lua
-- Category tem muitos Products
local Category = Model:extend({
    table = "categories",
    
    relations = {
        products = {
            type = "hasMany",
            model = "Product",
            foreign_key = "category_id"
        }
    }
})

-- Uso
local category = Category:find(1)
local products = category:products()  -- Array de produtos

for _, product in ipairs(products) do
    print(product.name)
end
```

### HasOne (1:1)

```lua
-- User tem um Profile
local User = Model:extend({
    table = "users",
    
    relations = {
        profile = {
            type = "hasOne",
            model = "Profile",
            foreign_key = "user_id"
        }
    }
})

-- Uso
local user = User:find(1)
local profile = user:profile()

print(profile.bio)
```

### BelongsToMany (N:N)

```lua
-- Product pertence a muitos Tags (via pivot)
local Product = Model:extend({
    table = "products",
    
    relations = {
        tags = {
            type = "belongsToMany",
            model = "Tag",
            pivot_table = "product_tags",
            foreign_key = "product_id",
            related_key = "tag_id"
        }
    }
})

-- Uso
local product = Product:find(1)
local tags = product:tags()

for _, tag in ipairs(tags) do
    print(tag.name)
end
```

### Eager Loading

```lua
-- N+1 Problem (ruim)
local products = Product:all()
for _, product in ipairs(products) do
    local category = product:category()  -- Query por produto!
end

-- Eager Loading (bom)
local products = Product:with('category'):get()
for _, product in ipairs(products) do
    print(product.category.name)  -- Já carregado!
end

-- Múltiplas relações
local products = Product:with('category', 'tags'):get()
```

---

## 🔄 Migrations

### Criar Migration

```bash
luvit crescent-cli make:migration create_products_table
```

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

### Migration de Alteração

```lua
-- migrations/20260109134500_add_discount_to_products.lua
local Migration = {}

function Migration:up()
    return [[
        ALTER TABLE products
        ADD COLUMN discount DECIMAL(5, 2) DEFAULT 0,
        ADD COLUMN is_featured BOOLEAN DEFAULT FALSE;
        
        CREATE INDEX idx_featured ON products(is_featured);
    ]]
end

function Migration:down()
    return [[
        ALTER TABLE products
        DROP COLUMN discount,
        DROP COLUMN is_featured;
        
        DROP INDEX idx_featured ON products;
    ]]
end

return Migration
```

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

### Hooks Disponíveis

```lua
local Product = Model:extend({
    table = "products",
    
    hooks = {
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
            self.slug = slugify(self.name)
        end,
        
        after_create = function(self)
            -- Depois de criar
            print("New product created!")
        end,
        
        before_update = function(self)
            -- Antes de atualizar
        end,
        
        after_update = function(self)
            -- Depois de atualizar
        end,
        
        before_delete = function(self)
            -- Antes de deletar
        end,
        
        after_delete = function(self)
            -- Depois de deletar
        end
    }
})
```

### Exemplo Prático

```lua
local Product = Model:extend({
    table = "products",
    
    hooks = {
        before_save = function(self)
            -- Gerar slug automaticamente
            if self.name and not self.slug then
                self.slug = self.name:lower():gsub("%s+", "-")
            end
        end,
        
        before_delete = function(self)
            -- Verificar se pode deletar
            local orderCount = OrderItem:where({product_id = self.id}):count()
            
            if orderCount > 0 then
                error("Cannot delete product with existing orders")
            end
        end,
        
        after_create = function(self)
            -- Notificar sistema
            EventBus:emit('product.created', self)
        end
    }
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

```lua
local db = require('crescent.database.mysql')

function OrderService:processOrder(orderData)
    db:query("START TRANSACTION")
    
    local success, err = pcall(function()
        -- Criar pedido
        local order = Order:create(orderData)
        
        -- Atualizar estoque
        for _, item in ipairs(orderData.items) do
            local product = Product:find(item.product_id)
            product:update({
                stock = product.stock - item.quantity
            })
        end
        
        -- Criar pagamento
        Payment:create({order_id = order.id, ...})
    end)
    
    if success then
        db:query("COMMIT")
        return true
    else
        db:query("ROLLBACK")
        error(err)
    end
end
```

### N+1 Problem

```lua
-- ❌ Ruim (N+1 queries)
local products = Product:all()
for _, product in ipairs(products) do
    local category = product:category()  -- +1 query por produto
end

-- ✅ Bom (2 queries)
local products = Product:with('category'):get()
for _, product in ipairs(products) do
    print(product.category.name)  -- Já carregado
end
```

### Paginação

```lua
-- No controller
function ProductController:index(ctx)
    local page = tonumber(ctx.query.page) or 1
    local perPage = tonumber(ctx.query.per_page) or 20
    
    local result = Product:paginate(perPage, page)
    
    return ctx.json(200, {
        data = result.data,
        current_page = result.current_page,
        total = result.total,
        per_page = result.per_page,
        last_page = result.last_page
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
        tests.assertError(function()
            Product:create({name = ""})  -- Empty name
        end)
    end,
    
    testRelations = function()
        local product = Product:find(1)
        local category = product:category()
        
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
