# 🎯 Conceitos Básicos

Entenda os principais componentes da arquitetura Crescent.

---

## 🛣️ Rotas

Rotas definem os endpoints da sua API e conectam URLs aos controllers.

### Definindo Rotas Básicas

```lua
-- app.lua
local Crescent = require('crescent')
local app = Crescent.create()

-- GET
app:get('/hello', function(ctx)
    return ctx.json(200, { message = "Hello World" })
end)

-- POST
app:post('/users', function(ctx)
    local body = ctx.body
    return ctx.json(201, body)
end)

-- PUT
app:put('/users/{id}', function(ctx)
    local id = ctx.params.id
    return ctx.json(200, { id = id })
end)

-- DELETE
app:delete('/users/{id}', function(ctx)
    local id = ctx.params.id
    return ctx.no_content()
end)

app:listen(8080)
```

### Parâmetros de Rota

```lua
-- Parâmetro único
app:get('/users/{id}', function(ctx)
    local id = ctx.params.id
    return ctx.json(200, { userId = id })
end)

-- Múltiplos parâmetros
app:get('/posts/{postId}/comments/{commentId}', function(ctx)
    local postId = ctx.params.postId
    local commentId = ctx.params.commentId
    return ctx.json(200, { postId = postId, commentId = commentId })
end)
```

### Query Parameters

```lua
app:get('/search', function(ctx)
    local query = ctx.query.q
    local page = ctx.query.page or 1
    local limit = ctx.query.limit or 10
    
    return ctx.json(200, {
        query = query,
        page = tonumber(page),
        limit = tonumber(limit)
    })
end)

-- GET /search?q=lua&page=2&limit=20
```

### Request Body

```lua
app:post('/users', function(ctx)
    local body = ctx.body
    
    -- Acessar campos
    local name = body.name
    local email = body.email
    
    return ctx.json(201, {
        name = name,
        email = email
    })
end)
```

### Organização em Arquivos

```lua
-- src/users/routes/users.lua
local controller = require("src.users.controllers.users")

return function(app, prefix)
    prefix = prefix or "/users"
    
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

### Registrar Rotas no App

```lua
-- app.lua
local userRoutes = require("src.users.routes.users")
userRoutes(app, "/api/users")
```

---

## 🎮 Controllers

Controllers recebem requisições HTTP e retornam respostas. Devem ser finos e delegar lógica para services.

### Estrutura Básica

```lua
-- src/users/controllers/users.lua
local service = require("src.users.services.users")
local UsersController = {}

function UsersController:index(ctx)
    local users = service:getAll()
    return ctx.json(200, users)
end

function UsersController:show(ctx)
    local id = ctx.params.id
    local user = service:getById(id)
    
    if user then
        return ctx.json(200, user)
    end
    
    return ctx.json(404, { error = "User not found" })
end

function UsersController:create(ctx)
    local body = ctx.body or {}
    
    -- Validação básica
    if not body.name or not body.email then
        return ctx.json(400, { error = "Name and email are required" })
    end
    
    local user = service:create(body)
    return ctx.json(201, user)
end

function UsersController:update(ctx)
    local id = ctx.params.id
    local body = ctx.body or {}
    
    local user = service:update(id, body)
    
    if user then
        return ctx.json(200, user)
    end
    
    return ctx.json(404, { error = "User not found" })
end

function UsersController:delete(ctx)
    local id = ctx.params.id
    local success = service:delete(id)
    
    if success then
        return ctx.no_content()
    end
    
    return ctx.json(404, { error = "User not found" })
end

return UsersController
```

### Context Object (ctx)

O objeto `ctx` contém toda informação da requisição:

```lua
function Controller:example(ctx)
    -- Parâmetros de rota
    local id = ctx.params.id
    
    -- Query parameters
    local page = ctx.query.page
    
    -- Request body
    local body = ctx.body
    
    -- Headers
    local auth = ctx.headers['authorization']
    
    -- Method
    local method = ctx.method  -- GET, POST, etc
    
    -- Path
    local path = ctx.path  -- /users/123
    
    -- Response helpers
    return ctx.json(200, data)
    return ctx.text(200, "Hello")
    return ctx.html(200, "<h1>Hello</h1>")
    return ctx.no_content()  -- 204
    return ctx.redirect(302, "/new-url")
end
```

### Validação no Controller

```lua
function UsersController:create(ctx)
    local body = ctx.body or {}
    
    -- Validação manual
    local errors = {}
    
    if not body.name or body.name == "" then
        table.insert(errors, "Name is required")
    end
    
    if not body.email or not string.match(body.email, ".+@.+%.%w+") then
        table.insert(errors, "Valid email is required")
    end
    
    if #errors > 0 then
        return ctx.json(422, { errors = errors })
    end
    
    -- Criar usuário
    local user = service:create(body)
    return ctx.json(201, user)
end
```

### Error Handling

```lua
function UsersController:create(ctx)
    local success, result = pcall(function()
        return service:create(ctx.body)
    end)
    
    if not success then
        -- Log error
        print("Error creating user:", result)
        
        return ctx.json(500, {
            error = "Internal server error",
            message = result
        })
    end
    
    return ctx.json(201, result)
end
```

---

## ⚙️ Services

Services contêm a lógica de negócio da aplicação. Devem ser independentes de HTTP.

### Estrutura Básica

```lua
-- src/users/services/users.lua
local UsersService = {}
local User = require("src.users.models.user")

function UsersService:getAll()
    return User:all()
end

function UsersService:getById(id)
    return User:find(id)
end

function UsersService:create(data)
    -- Validação adicional
    if not data.name or #data.name < 3 then
        error("Name must be at least 3 characters")
    end
    
    return User:create(data)
end

function UsersService:update(id, data)
    local user = User:find(id)
    
    if not user then
        return nil
    end
    
    user:update(data)
    return user
end

function UsersService:delete(id)
    local user = User:find(id)
    
    if not user then
        return false
    end
    
    user:delete()
    return true
end

return UsersService
```

### Lógica de Negócio Complexa

```lua
-- src/orders/services/orders.lua
local OrdersService = {}
local Order = require("src.orders.models.order")
local Product = require("src.products.models.product")
local User = require("src.users.models.user")

function OrdersService:createOrder(userId, items)
    -- Validar usuário
    local user = User:find(userId)
    if not user then
        error("User not found")
    end
    
    -- Validar produtos e calcular total
    local total = 0
    local validatedItems = {}
    
    for _, item in ipairs(items) do
        local product = Product:find(item.productId)
        
        if not product then
            error("Product " .. item.productId .. " not found")
        end
        
        if product.stock < item.quantity then
            error("Insufficient stock for " .. product.name)
        end
        
        local subtotal = product.price * item.quantity
        total = total + subtotal
        
        table.insert(validatedItems, {
            product_id = product.id,
            quantity = item.quantity,
            price = product.price,
            subtotal = subtotal
        })
    end
    
    -- Criar pedido
    local order = Order:create({
        user_id = userId,
        total = total,
        status = "pending"
    })
    
    -- Adicionar itens ao pedido
    for _, item in ipairs(validatedItems) do
        order:addItem(item)
        
        -- Atualizar estoque
        local product = Product:find(item.product_id)
        product:update({
            stock = product.stock - item.quantity
        })
    end
    
    return order
end

function OrdersService:cancelOrder(orderId)
    local order = Order:find(orderId)
    
    if not order then
        error("Order not found")
    end
    
    if order.status ~= "pending" then
        error("Only pending orders can be cancelled")
    end
    
    -- Devolver produtos ao estoque
    local items = order:items()
    
    for _, item in ipairs(items) do
        local product = Product:find(item.product_id)
        product:update({
            stock = product.stock + item.quantity
        })
    end
    
    -- Atualizar status
    order:update({ status = "cancelled" })
    
    return order
end

return OrdersService
```

### Services com Transações

```lua
function OrdersService:processPayment(orderId, paymentData)
    local db = require('crescent.database.mysql')
    
    -- Iniciar transação
    db:query("START TRANSACTION")
    
    local success, err = pcall(function()
        local order = Order:find(orderId)
        
        if not order then
            error("Order not found")
        end
        
        -- Processar pagamento (API externa)
        local paymentResult = PaymentGateway:charge(paymentData)
        
        if not paymentResult.success then
            error("Payment failed: " .. paymentResult.error)
        end
        
        -- Atualizar pedido
        order:update({
            status = "paid",
            payment_id = paymentResult.id
        })
        
        -- Enviar email de confirmação
        EmailService:sendOrderConfirmation(order)
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

---

## 💾 Models (Básico)

Models representam dados e interagem com o banco via ORM ActiveRecord.

### Definição Básica

```lua
-- src/users/models/user.lua
local Model = require("crescent.database.model")

local User = Model:extend({
    table = "users",
    primary_key = "id",
    timestamps = true,
    
    fillable = {
        "name",
        "email",
        "password"
    },
    
    hidden = {
        "password"
    },
    
    validates = {
        name = { required = true, min = 3, max = 100 },
        email = { required = true, email = true, unique = true },
        password = { required = true, min = 6 }
    }
})

return User
```

### Operações CRUD

```lua
-- CREATE
local user = User:create({
    name = "John Doe",
    email = "john@example.com",
    password = "hashed_password"
})

-- READ
local user = User:find(1)
local users = User:all()
local user = User:where({email = "john@example.com"}):first()

-- UPDATE
user:update({name = "Jane Doe"})

-- DELETE
user:delete()
```

Para mais detalhes sobre Models, veja [Database & ORM](/docs/database).

---

## 🔒 Middleware

Middleware processa requisições antes que cheguem aos controllers.

### Middleware de Autenticação

```lua
-- crescent/middleware/auth.lua
local Auth = {}

function Auth.middleware(ctx, next)
    local token = ctx.headers['authorization']
    
    if not token then
        return ctx.json(401, { error = "No token provided" })
    end
    
    -- Validar token
    local user = validateToken(token)
    
    if not user then
        return ctx.json(401, { error = "Invalid token" })
    end
    
    -- Adicionar usuário ao contexto
    ctx.user = user
    
    -- Continuar para próximo middleware/controller
    return next()
end

return Auth
```

### Aplicar Middleware

```lua
-- app.lua
local auth = require('crescent.middleware.auth')

-- Global (todas as rotas)
app:use(auth.middleware)

-- Específico para rota
app:get('/protected', auth.middleware, function(ctx)
    return ctx.json(200, { user = ctx.user })
end)
```

### Middleware de Logging

```lua
-- crescent/middleware/logger.lua
local Logger = {}

function Logger.middleware(ctx, next)
    local start = os.clock()
    
    -- Log request
    print(string.format("[%s] %s %s", os.date(), ctx.method, ctx.path))
    
    -- Executar próximo
    local response = next()
    
    -- Log response time
    local duration = (os.clock() - start) * 1000
    print(string.format("  → %d (%dms)", response.status or 200, duration))
    
    return response
end

return Logger
```

### Middleware CORS

```lua
-- crescent/middleware/cors.lua
local CORS = {}

function CORS.middleware(ctx, next)
    -- Adicionar headers CORS
    ctx.headers['Access-Control-Allow-Origin'] = '*'
    ctx.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    ctx.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    -- Handle preflight
    if ctx.method == 'OPTIONS' then
        return ctx.no_content()
    end
    
    return next()
end

return CORS
```

### Ordem dos Middlewares

```lua
-- app.lua
local cors = require('crescent.middleware.cors')
local logger = require('crescent.middleware.logger')
local auth = require('crescent.middleware.auth')

-- Ordem importa!
app:use(cors.middleware)      -- 1. CORS primeiro
app:use(logger.middleware)    -- 2. Logging
app:use(auth.middleware)      -- 3. Auth por último

-- Rotas
app:get('/api/users', usersController.index)
```

---

## 🏗️ Módulos

Módulos agrupam funcionalidades relacionadas (controllers, services, models, routes).

### Estrutura de Módulo

```
src/users/
├── init.lua                 # Registrador do módulo
├── controllers/
│   └── users.lua
├── services/
│   └── users.lua
├── models/
│   └── user.lua
└── routes/
    └── users.lua
```

### Module Init

```lua
-- src/users/init.lua
local Module = {}

function Module.register(app)
    -- Registrar rotas
    local routes = require("src.users.routes.users")
    routes(app, "/api/users")
    
    print("✓ Módulo Users carregado")
end

return Module
```

### Registrar no App

```lua
-- app.lua
local Crescent = require('crescent')
local app = Crescent.create()

-- Registrar módulos
local UsersModule = require("src.users")
local ProductsModule = require("src.products")

UsersModule.register(app)
ProductsModule.register(app)

app:listen(8080)
```

### Gerar Módulo via CLI

```bash
luvit crescent-cli make:module Product
```

Cria toda a estrutura automaticamente!

---

## 📊 Fluxo de Requisição

```
Cliente HTTP
    ↓
[Middleware CORS]
    ↓
[Middleware Logger]
    ↓
[Middleware Auth]
    ↓
[Router] → Encontra rota
    ↓
[Controller] → Recebe requisição
    ↓
[Service] → Lógica de negócio
    ↓
[Model/ORM] → Banco de dados
    ↓
[Service] ← Retorna dados
    ↓
[Controller] ← Formata resposta
    ↓
Cliente HTTP ← JSON response
```

---

## 💡 Boas Práticas

### Controllers

- ✅ Mantenha finos (thin controllers)
- ✅ Delegue lógica para services
- ✅ Valide entrada básica
- ✅ Trate erros com try/catch (pcall)
- ✅ Retorne status codes apropriados

### Services

- ✅ Lógica de negócio aqui
- ✅ Independente de HTTP
- ✅ Reutilizável entre controllers
- ✅ Use transações quando necessário
- ✅ Valide regras de negócio

### Rotas

- ✅ Use padrões RESTful
- ✅ Agrupe por prefixo (`/api/v1`)
- ✅ Organize em arquivos separados
- ✅ Use nomes descritivos

### Middleware

- ✅ Ordem importa
- ✅ CORS primeiro
- ✅ Auth/validação depois
- ✅ Use `next()` para continuar

---

## 🧪 Testando Componentes

```lua
-- tests/test-users.lua
local tests = require('crescent.utils.tests')
local UsersService = require('src.users.services.users')

local userTests = {
    testCreate = function()
        local user = UsersService:create({
            name = "Test User",
            email = "test@example.com"
        })
        
        tests.assertNotNil(user)
        tests.assertEquals(user.name, "Test User")
    end,
    
    testValidation = function()
        tests.assertError(function()
            UsersService:create({ name = "AB" })  -- Too short
        end, "at least 3 characters")
    end
}

tests.runSuite("Users Service Tests", userTests)
```

---

## 📖 Próximas Seções

- **[Database & ORM](/docs/database)** - Models em detalhes
- **[Utilities](/docs/utilities)** - Testes e helpers
- **[CLI](/docs/cli)** - Geradores de código
