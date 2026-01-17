# 🔧 Utilidades

Crescent fornece diversas utilidades prontas para acelerar seu desenvolvimento.

---

## ✅ Sistema de Testes

O Crescent inclui uma biblioteca completa de assertions para testes automatizados.

### Criar Arquivo de Teste

```lua
-- tests/test-users.lua
local tests = require('crescent.utils.tests')

local userTests = {
    testCreate = function()
        -- Seu código de teste
        tests.assertEquals(1 + 1, 2)
    end,
    
    testValidation = function()
        tests.assertTrue(true)
        tests.assertFalse(false)
    end
}

tests.runSuite("User Tests", userTests)
```

### Executar Testes

```bash
# Todos os testes
luvit crescent-cli test

# Teste específico
luvit tests/test-users.lua
```

---

## 📋 Assertions Disponíveis

### Comparações Básicas

```lua
-- Igualdade
tests.assertEquals(actual, expected, "mensagem opcional")
tests.assertNotEquals(actual, expected)

-- Booleanos
tests.assertTrue(value)
tests.assertFalse(value)
```

### Comparações Numéricas

```lua
tests.assertGreaterThan(5, 3)        -- 5 > 3
tests.assertLessThan(3, 5)           -- 3 < 5
tests.assertGreaterOrEqual(5, 5)     -- 5 >= 5
tests.assertLessOrEqual(3, 5)        -- 3 <= 5
tests.assertInRange(5, 1, 10)        -- 1 <= 5 <= 10
```

### Validações de Tipo

```lua
tests.assertType(value, "string")
tests.assertNil(value)
tests.assertNotNil(value)
tests.assertIsTable(value)
tests.assertIsFunction(value)
tests.assertIsString(value)
tests.assertIsNumber(value)
tests.assertIsBoolean(value)
```

### Comparações de Strings

```lua
tests.assertContains("hello world", "world")
tests.assertNotContains("hello", "bye")
tests.assertStartsWith("hello world", "hello")
tests.assertEndsWith("hello world", "world")
tests.assertMatches("test123", "%d+")  -- Lua pattern
```

### Comparações de Tables

```lua
-- Comparação profunda
tests.assertTableEquals({a=1, b=2}, {a=1, b=2})

-- Contém valor
tests.assertTableContains({1, 2, 3}, 2)

-- Vazio/não vazio
tests.assertEmpty({})
tests.assertNotEmpty({1})

-- Tamanho
tests.assertLength({1, 2, 3}, 3)
tests.assertArrayLength({1, 2, 3}, 3)
```

### Exceptions/Errors

```lua
-- Espera erro
tests.assertError(function()
    error("Ops!")
end, "Ops!")

-- Não deve dar erro
tests.assertNoError(function()
    return 1 + 1
end)
```

### HTTP/API Testing

```lua
-- Status code
tests.assertStatusCode(response, 200)

-- Headers
tests.assertHeader(response, "Content-Type", "application/json")

-- JSON response
tests.assertJsonEquals('{"name":"John"}', {name="John"})
tests.assertJsonContains('{"name":"John","age":30}', "name", "John")
```

### Identidade

```lua
local obj = {}
tests.assertSame(obj, obj)        -- Mesma referência
tests.assertNotSame({}, {})       -- Objetos diferentes
```

---

## 📝 Exemplo Completo de Teste

```lua
-- tests/test-product.lua
local tests = require('crescent.utils.tests')
local Product = require('src.products.models.product')

local productTests = {
    testCreate = function()
        local product = Product:create({
            name = "Notebook",
            price = 2500
        })
        
        tests.assertNotNil(product)
        tests.assertIsTable(product)
        tests.assertEquals(product.name, "Notebook")
        tests.assertType(product.price, "number")
        tests.assertGreaterThan(product.price, 0)
    end,
    
    testValidation = function()
        tests.assertError(function()
            Product:create({name = ""})  -- Nome vazio
        end, "validation failed")
    end,
    
    testFind = function()
        local product = Product:find(1)
        
        if product then
            tests.assertIsTable(product)
            tests.assertNotNil(product.id)
            tests.assertType(product.name, "string")
        end
    end,
    
    testUpdate = function()
        local product = Product:find(1)
        
        if product then
            local oldName = product.name
            product:update({name = "Updated Name"})
            
            tests.assertNotEquals(product.name, oldName)
            tests.assertEquals(product.name, "Updated Name")
        end
    end,
    
    testAll = function()
        local products = Product:all()
        
        tests.assertIsTable(products)
        tests.assertGreaterOrEqual(#products, 0)
    end
}

-- Executar suite
tests.runSuite("Product Tests", productTests)
```

**Saída:**
```
=== Test Suite: Product Tests ===
Running test: testCreate
✅ testCreate passed
Running test: testValidation
✅ testValidation passed
Running test: testFind
✅ testFind passed
Running test: testUpdate
✅ testUpdate passed
Running test: testAll
✅ testAll passed

=== Results: 5/5 passed, 0 failed ===
```

---

## 🔐 Hash de Senhas (PBKDF2)

Utilitário seguro para hash de senhas com salt aleatório.

### Características

- ✅ PBKDF2 com SHA-256
- ✅ Salt aleatório único (16 bytes)
- ✅ 10.000 iterações por padrão
- ✅ Timing-safe comparison
- ✅ Senhas iguais geram hashes diferentes

### Criar Hash de Senha

```lua
local hash = require('crescent.utils.hash')

-- Registrar usuário
local senha = "minhaSenhaSegura123"
local senhaHash = hash.encrypt(senha)
-- Resultado: "10000$a1b2c3d4e5f6...$9c8d7e6f5a4b..."

-- Armazenar senhaHash no banco de dados
user:update({password = senhaHash})
```

### Verificar Senha (Login)

```lua
local hash = require('crescent.utils.hash')

-- No login
local senhaDigitada = ctx.body.password
local senhaArmazenada = user.password  -- Hash do banco

if hash.verify(senhaDigitada, senhaArmazenada) then
    -- Login bem-sucedido
    return ctx.json(200, {token = gerarToken(user)})
else
    -- Senha incorreta
    return ctx.json(401, {error = "Credenciais inválidas"})
end
```

### Exemplo Completo (Registro + Login)

```lua
-- src/auth/services/auth.lua
local hash = require('crescent.utils.hash')
local User = require('src.users.models.user')

local AuthService = {}

function AuthService:register(data)
    -- Valida dados
    if not data.email or not data.password then
        error("Email e senha são obrigatórios")
    end
    
    -- Cria hash da senha
    local passwordHash = hash.encrypt(data.password)
    
    -- Cria usuário
    local user = User:create({
        name = data.name,
        email = data.email,
        password = passwordHash  -- Armazena hash, não senha
    })
    
    return user
end

function AuthService:login(email, password)
    -- Busca usuário
    local user = User:where({email = email}):first()
    
    if not user then
        return nil, "Usuário não encontrado"
    end
    
    -- Verifica senha
    if not hash.verify(password, user.password) then
        return nil, "Senha incorreta"
    end
    
    -- Remove senha do retorno
    user.password = nil
    
    return user
end

return AuthService
```

### Configurar Iterações

```lua
-- Mais seguro (mais lento)
local hash50k = hash.encrypt(senha, 50000)

-- Padrão (balanceado)
local hashPadrao = hash.encrypt(senha)  -- 10.000 iterações
```

### Aliases Disponíveis

```lua
-- Estas são equivalentes:
hash.encrypt(senha)   -- ✅ Recomendado
hash.encript(senha)   -- Alias (typo comum)

hash.verify(senha, hash)   -- ✅ Recomendado  
hash.decrypt(senha, hash)  -- Alias
hash.decript(senha, hash)  -- Alias
```

### Hashes Simples (Checksums)

```lua
-- SHA-256 (para checksums, não senhas!)
local checksum = hash.sha256("conteúdo do arquivo")

-- MD5 (legado, não usar para senhas)
local md5sum = hash.md5("dados")
```

⚠️ **Importante:** Nunca use SHA-256 ou MD5 direto para senhas! Sempre use `hash.encrypt()` que implementa PBKDF2 com salt.

---

## 🔐 JWT (JSON Web Tokens)

O Crescent fornece suporte completo para autenticação JWT sem dependências externas, usando apenas funções nativas do OpenResty.

### Configurar JWT Secret

Adicione no seu `.env`:

```bash
JWT_SECRET=sua_chave_secreta_super_segura_com_64_ou_mais_caracteres
```

### Gerar Token

```lua
local jwt = require('crescent.utils.jwt')

-- Payload do token
local payload = {
    user_id = 1,
    username = "joao",
    email = "joao@example.com",
    roles = {"user", "admin"}
}

-- Gerar token (expira em 15 minutos por padrão)
local token = jwt.sign(payload, os.getenv('JWT_SECRET'), {
    expiresIn = 900  -- 15 minutos em segundos
})

-- Retornar para o cliente
return ctx.json(200, {
    token = token,
    type = "Bearer"
})
```

### Verificar Token

```lua
local jwt = require('crescent.utils.jwt')

-- Obter token do header Authorization
local token = ctx.getBearer()  -- Remove "Bearer " automaticamente

-- Verificar e decodificar
local ok, payload_or_error = jwt.verify(token, os.getenv('JWT_SECRET'))

if ok then
    -- Token válido
    local user_id = payload_or_error.user_id
    local username = payload_or_error.username
    -- ... usar dados
else
    -- Token inválido
    return ctx.error(401, payload_or_error)
end
```

### Opções Avançadas

```lua
local jwt = require('crescent.utils.jwt')

-- Token com claims adicionais
local token = jwt.sign(payload, secret, {
    expiresIn = 3600,           -- Expira em 1 hora
    notBefore = 0,              -- Válido imediatamente
    issuer = "crescent-app",    -- Quem emitiu
    audience = "api-users"      -- Para quem é destinado
})

-- Verificar com validação de claims
local ok, payload = jwt.verify(token, secret, {
    issuer = "crescent-app",    -- Valida issuer
    audience = "api-users"      -- Valida audience
})
```

### Access Token e Refresh Token

```lua
local jwt = require('crescent.utils.jwt')

local payload = {
    user_id = 1,
    username = "joao"
}

-- Access token (curta duração - 15 min)
local access_token = jwt.create_access_token(
    payload, 
    os.getenv('JWT_SECRET'),
    900  -- 15 minutos (opcional, padrão já é 15min)
)

-- Refresh token (longa duração - 30 dias)
local refresh_token = jwt.create_refresh_token(
    payload,
    os.getenv('JWT_SECRET'),
    2592000  -- 30 dias (opcional, padrão já é 30 dias)
)

return ctx.json(200, {
    access_token = access_token,
    refresh_token = refresh_token,
    token_type = "Bearer",
    expires_in = 900
})
```

### Decodificar Sem Verificar

```lua
local jwt = require('crescent.utils.jwt')

-- Apenas para debug/inspeção - NÃO use para autenticação!
local header, payload = jwt.decode(token)

print("Algorithm:", header.alg)  -- "HS256"
print("User ID:", payload.user_id)
-- ⚠️ Assinatura NÃO foi verificada!
```

### Middleware de Autenticação JWT

```lua
local auth = require('crescent.middleware.auth')

-- Middleware JWT básico
app:use('/api/protected', auth.jwt())

-- Com opções customizadas
app:use('/api/admin', auth.jwt({
    secret = os.getenv('JWT_SECRET'),
    issuer = "crescent-app",
    audience = "admin-panel",
    getUserFromPayload = function(payload, ctx)
        -- Buscar usuário completo do banco
        return User:find(payload.user_id)
    end
}))

-- Usar dados do usuário na rota
app:get('/api/profile', function(ctx)
    -- ctx.state.user foi populado pelo middleware
    local user = ctx.state.user
    return ctx.json(200, {
        id = user.id,
        name = user.name,
        email = user.email
    })
end)
```

### Helpers do Middleware Auth

```lua
local auth = require('crescent.middleware.auth')

-- Gerar token manualmente
local token = auth.generate_token({
    user_id = 1,
    username = "joao"
}, {
    secret = os.getenv('JWT_SECRET'),
    expiresIn = 3600
})

-- Gerar par de tokens (access + refresh)
local tokens = auth.generate_token_pair({
    user_id = 1,
    username = "joao"
}, {
    secret = os.getenv('JWT_SECRET'),
    access_expires_in = 900,      -- 15 min
    refresh_expires_in = 2592000  -- 30 dias
})

-- tokens = {
--     access_token = "eyJ...",
--     refresh_token = "eyJ...",
--     token_type = "Bearer",
--     expires_in = 900
-- }

-- Verificar token fora do middleware
local ok, payload = auth.verify_token(token, {
    secret = os.getenv('JWT_SECRET')
})

-- Decodificar sem verificar (debug)
local header, payload = auth.decode_token(token)
```

### Exemplo Completo: Sistema de Auth

```lua
-- src/auth/services/auth.lua
local jwt = require('crescent.utils.jwt')
local hash = require('crescent.utils.hash')
local User = require('src.users.models.user')

local AuthService = {}

-- Registro de usuário
function AuthService.register(data)
    -- Validar dados
    if not data.email or not data.password then
        error("Email e senha são obrigatórios")
    end
    
    -- Hash da senha
    local passwordHash = hash.encrypt(data.password)
    
    -- Criar usuário
    local user = User:create({
        name = data.name,
        email = data.email,
        password = passwordHash
    })
    
    -- Gerar tokens
    local tokens = AuthService.generateTokens(user)
    
    return {
        user = {
            id = user.id,
            name = user.name,
            email = user.email
        },
        tokens = tokens
    }
end

-- Login de usuário
function AuthService.login(email, password)
    -- Buscar usuário
    local user = User:where({email = email}):first()
    
    if not user then
        error("Credenciais inválidas")
    end
    
    -- Verificar senha
    if not hash.verify(password, user.password) then
        error("Credenciais inválidas")
    end
    
    -- Gerar tokens
    local tokens = AuthService.generateTokens(user)
    
    return {
        user = {
            id = user.id,
            name = user.name,
            email = user.email
        },
        tokens = tokens
    }
end

-- Refresh token
function AuthService.refresh(refresh_token)
    local secret = os.getenv('JWT_SECRET')
    
    -- Verificar refresh token
    local ok, payload = jwt.verify(refresh_token, secret)
    
    if not ok then
        error("Token inválido ou expirado")
    end
    
    -- Buscar usuário
    local user = User:find(payload.user_id)
    
    if not user then
        error("Usuário não encontrado")
    end
    
    -- Gerar novo access token
    local access_token = jwt.create_access_token({
        user_id = user.id,
        username = user.name,
        email = user.email
    }, secret)
    
    return {
        access_token = access_token,
        token_type = "Bearer",
        expires_in = 900
    }
end

-- Helper para gerar tokens
function AuthService.generateTokens(user)
    local secret = os.getenv('JWT_SECRET')
    
    local payload = {
        user_id = user.id,
        username = user.name,
        email = user.email
    }
    
    local access_token = jwt.create_access_token(payload, secret)
    local refresh_token = jwt.create_refresh_token(payload, secret)
    
    return {
        access_token = access_token,
        refresh_token = refresh_token,
        token_type = "Bearer",
        expires_in = 900
    }
end

return AuthService
```

### Rotas de Autenticação

```lua
-- src/auth/routes/auth.lua
local AuthService = require('src.auth.services.auth')

return function(app)
    -- Registro
    app:post('/auth/register', function(ctx)
        local data = ctx.body
        
        local ok, result = pcall(function()
            return AuthService.register(data)
        end)
        
        if not ok then
            return ctx.json(400, {error = result})
        end
        
        return ctx.json(201, result)
    end)
    
    -- Login
    app:post('/auth/login', function(ctx)
        local data = ctx.body
        
        local ok, result = pcall(function()
            return AuthService.login(data.email, data.password)
        end)
        
        if not ok then
            return ctx.json(401, {error = result})
        end
        
        return ctx.json(200, result)
    end)
    
    -- Refresh token
    app:post('/auth/refresh', function(ctx)
        local refresh_token = ctx.body.refresh_token
        
        if not refresh_token then
            return ctx.json(400, {error = "Refresh token é obrigatório"})
        end
        
        local ok, result = pcall(function()
            return AuthService.refresh(refresh_token)
        end)
        
        if not ok then
            return ctx.json(401, {error = result})
        end
        
        return ctx.json(200, result)
    end)
    
    -- Profile (protegida)
    local auth = require('crescent.middleware.auth')
    
    app:get('/auth/profile', auth.jwt(), function(ctx)
        local user = ctx.state.user
        return ctx.json(200, {
            id = user.id,
            name = user.name,
            email = user.email
        })
    end)
    
    -- Logout (opcional - invalidar no cliente)
    app:post('/auth/logout', auth.jwt(), function(ctx)
        -- Em produção, considere blacklist de tokens
        return ctx.json(200, {message = "Logout realizado"})
    end)
end
```

### Claims Padrão JWT

| Claim | Descrição | Exemplo |
|-------|-----------|---------|
| `iat` | Issued At - quando foi criado | `1705484400` |
| `exp` | Expiration - quando expira | `1705488000` |
| `nbf` | Not Before - válido a partir de | `1705484400` |
| `iss` | Issuer - quem emitiu | `"crescent-app"` |
| `aud` | Audience - para quem é destinado | `"api-users"` |

### Boas Práticas JWT

✅ **Recomendado:**

- Use secrets longos e aleatórios (64+ caracteres)
- Access tokens curtos (15 min)
- Refresh tokens longos (30 dias)
- Armazene tokens com segurança no cliente (HttpOnly cookies)
- Valide claims como `issuer` e `audience`
- Implemente refresh token rotation

❌ **Evite:**

- Armazenar dados sensíveis no payload (é decodificável!)
- Tokens muito longos (> 7 dias para access)
- Reutilizar JWT secret entre ambientes
- Esquecer de validar expiração
- Confiar apenas no token sem validar usuário no banco

### Testar JWT

```lua
-- tests/test-jwt.lua
local tests = require('crescent.utils.tests')
local jwt = require('crescent.utils.jwt')

local secret = "test_secret_key"

local jwtTests = {
    testSignAndVerify = function()
        local payload = {user_id = 1}
        local token = jwt.sign(payload, secret)
        
        local ok, decoded = jwt.verify(token, secret)
        tests.assertTrue(ok)
        tests.assertEquals(decoded.user_id, 1)
    end,
    
    testInvalidSignature = function()
        local payload = {user_id = 1}
        local token = jwt.sign(payload, secret)
        
        local ok, error = jwt.verify(token, "wrong_secret")
        tests.assertFalse(ok)
        tests.assertNotNil(error)
    end,
    
    testExpiration = function()
        local payload = {user_id = 1}
        local token = jwt.sign(payload, secret, {expiresIn = 1})
        
        local ok = jwt.verify(token, secret)
        tests.assertTrue(ok)
        -- Token expira após 1 segundo
    end
}

tests.runSuite("JWT Tests", jwtTests)
```

---

## 🌐 Variáveis de Ambiente

```lua
local env = require('crescent.utils.env')

-- Carregar .env
env.load('.env')

-- Obter valores
local dbHost = env.get('DB_HOST', 'localhost')  -- Com fallback
local port = env.get('PORT')
local isDev = env.get('ENV') == 'development'

-- Verificar se existe
if env.has('API_KEY') then
    -- usa API_KEY
end
```

---

## 📨 Headers HTTP

```lua
local headers = require('crescent.utils.headers')

-- Parse header string
local contentType = headers.parse('Content-Type: application/json')

-- Normalize header name
local normalized = headers.normalize('content-type')  -- "Content-Type"

-- Get header value
local value = headers.get(ctx.headers, 'authorization')
```

---

## 🛤️ Path Utilities

```lua
local pathUtil = require('crescent.utils.path')

-- Join paths
local fullPath = pathUtil.join('src', 'users', 'models', 'user.lua')
-- "src/users/models/user.lua"

-- Normalize path
local normalized = pathUtil.normalize('src//users/../models/./user.lua')
-- "src/models/user.lua"

-- Get directory
local dir = pathUtil.dirname('src/users/models/user.lua')
-- "src/users/models"

-- Get filename
local file = pathUtil.basename('src/users/models/user.lua')
-- "user.lua"

-- Get extension
local ext = pathUtil.extname('user.lua')
-- ".lua"
```

---

## 🔤 String Utilities

```lua
local stringUtil = require('crescent.utils.string')

-- Trim whitespace
local trimmed = stringUtil.trim('  hello  ')  -- "hello"

-- Split string
local parts = stringUtil.split('a,b,c', ',')  -- {"a", "b", "c"}

-- Starts/ends with
local starts = stringUtil.startsWith('hello', 'hel')  -- true
local ends = stringUtil.endsWith('hello', 'lo')  -- true

-- Case transformations
local upper = stringUtil.upper('hello')  -- "HELLO"
local lower = stringUtil.lower('HELLO')  -- "hello"
local title = stringUtil.titleCase('hello world')  -- "Hello World"

-- Slugify
local slug = stringUtil.slugify('Hello World!')  -- "hello-world"
```

---

## 🧪 Testando Utilities

```lua
-- tests/test-utilities.lua
local tests = require('crescent.utils.tests')
local hash = require('crescent.utils.hash')
local stringUtil = require('crescent.utils.string')

local utilTests = {
    testHashUnique = function()
        local senha = "test123"
        local hash1 = hash.encrypt(senha)
        local hash2 = hash.encrypt(senha)
        
        -- Hashes devem ser diferentes (salt único)
        tests.assertNotEquals(hash1, hash2)
        
        -- Mas ambos devem verificar corretamente
        tests.assertTrue(hash.verify(senha, hash1))
        tests.assertTrue(hash.verify(senha, hash2))
    end,
    
    testHashVerification = function()
        local senha = "myPassword123"
        local hashed = hash.encrypt(senha)
        
        tests.assertTrue(hash.verify(senha, hashed))
        tests.assertFalse(hash.verify("wrongPassword", hashed))
    end,
    
    testStringTrim = function()
        tests.assertEquals(stringUtil.trim("  hello  "), "hello")
        tests.assertEquals(stringUtil.trim("hello"), "hello")
    end,
    
    testStringSplit = function()
        local parts = stringUtil.split("a,b,c", ",")
        tests.assertArrayLength(parts, 3)
        tests.assertEquals(parts[1], "a")
        tests.assertEquals(parts[3], "c")
    end
}

tests.runSuite("Utility Tests", utilTests)
```

---

## 💡 Boas Práticas

### Testes

1. **Organize por módulo**: `tests/test-{module}.lua`
2. **Nomenclatura clara**: `testCreate`, `testValidation`
3. **Um assert por conceito**: Testes pequenos e focados
4. **Use mensagens descritivas**: Facilita debug
5. **Rode antes de commit**: `git pre-commit hook`

### Hash de Senhas

1. **Nunca armazene senhas em texto plano**
2. **Use `hash.encrypt()` sempre**: PBKDF2 + salt
3. **Não use SHA-256/MD5 para senhas**
4. **Valide força da senha antes**: regex, tamanho mínimo
5. **Considere 2FA para produção**

### Variáveis de Ambiente

1. **Nunca commite `.env`**: Use `.env.example`
2. **Use fallbacks**: `env.get('PORT', 8080)`
3. **Valide valores críticos**: MySQL, API keys
4. **Diferentes arquivos por ambiente**: `.env.dev`, `.env.prod`

---

## 📖 Próximas Seções

- **[Database & ORM](/docs/database)** - Models, relações e migrations
- **[Core Concepts](/docs/core-concepts)** - Rotas, controllers e services
- **[Deployment](/docs/deployment)** - Deploy em produção
