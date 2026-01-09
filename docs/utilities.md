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
