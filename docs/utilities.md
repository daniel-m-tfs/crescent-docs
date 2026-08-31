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

# Um arquivo específico
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
        -- Product:create() não lança erro em validação inválida —
        -- devolve nil + uma tabela de erros (retorno múltiplo)
        local product, errors = Product:create({name = ""})

        tests.assertNil(product)
        tests.assertNotNil(errors)
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
    -- Busca usuário (where() é posicional: coluna, [operador,] valor)
    local user = User:where("email", email):first()
    
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

### Hashes Simples (Checksums)

```lua
-- SHA-256 (para checksums, não senhas!)
local checksum = hash.sha256("conteúdo do arquivo")

-- MD5 (legado, não usar para senhas)
local md5sum = hash.md5("dados")
```

⚠️ **Importante:** Nunca use SHA-256 ou MD5 direto para senhas! Sempre use `hash.encrypt()` que implementa PBKDF2 com salt.

> `hash.encrypt()`/`hash.verify()` são os únicos nomes válidos hoje — os
> aliases antigos (`encript`, `decrypt`, `decript`) foram removidos.

---

## 🌐 APIs Externas

`crescent.utils.http` é um cliente HTTP estilo axios para consumir APIs
externas, construído sobre `socket.http`/`ssl.https`/`ltn12`/`cjson`
(dependências LuaRocks: `luasocket`, `luasec`, `lua-cjson`).

### Uso Básico (instância padrão)

```lua
local http = require('crescent.utils.http')

-- GET
local result, err = http.get("https://api.exemplo.com/users/1")
if result then
    print(result.status)   -- 200
    print(result.data)     -- corpo já decodificado como tabela se for JSON
else
    print(err.message)     -- "Request failed with status 404"
end

-- POST com corpo JSON (Content-Type: application/json é setado automaticamente)
local result, err = http.post("https://api.exemplo.com/users", {
    name = "João",
    email = "joao@example.com"
})

-- PUT / PATCH / DELETE / HEAD / OPTIONS
http.put(url, data)
http.patch(url, data)
http.delete(url)
http.head(url)
http.options(url)

-- Requisição genérica
local result, err = http.request({
    url = "https://api.exemplo.com/search",
    method = "GET",
    params = { q = "crescent" },   -- vira ?q=crescent na URL
    headers = { ["x-api-key"] = "..." }
})
```

Retorno: em sucesso, `(result, nil)` — `result` tem `data` (corpo, já
decodificado se for JSON válido), `status`, `statusText`, `headers`,
`config`, `request`. Em falha, `(nil, result)` — o mesmo formato, mais
`result.error = true` e `result.message`.

### Instância customizada (baseURL, headers e timeout fixos)

```lua
local http = require('crescent.utils.http')

local api = http.create({
    baseURL = "https://api.exemplo.com",
    timeout = 10,
    headers = { ["Authorization"] = "Bearer " .. token }
})

local result, err = api:get("/users/1")  -- vira https://api.exemplo.com/users/1
local result, err = api:post("/users", { name = "João" })
```

---

## 🔐 JWT (JSON Web Tokens)

O Crescent fornece suporte a autenticação JWT no runtime **Luvit** (não
OpenResty/nginx — são runtimes Lua diferentes). `crescent.utils.jwt` tenta
usar `openssl.hmac.digest` para o HMAC-SHA256 quando disponível (o módulo
`openssl` já vem embutido no binário do Luvit — confirme com `luvit -v`) e
cai para uma implementação SHA-256 pure-Lua automaticamente caso contrário,
então funciona sem dependências extras de qualquer forma.

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

Middlewares no Crescent são sempre **globais** (`app:use(middleware)`, sem
segundo argumento de path) — não existe middleware escopado por rota. Para
proteger só parte das rotas, registre o middleware depois das rotas
públicas e antes das rotas protegidas, ou monte um sub-app/roteador
separado por módulo.

```lua
local auth = require('crescent.middleware.auth')

-- Middleware JWT básico (protege tudo que for registrado depois dele)
app:use(auth.jwt())

-- Com opções customizadas
app:use(auth.jwt({
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
    -- Buscar usuário (where() é posicional)
    local user = User:where("email", email):first()
    
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
local auth = require('crescent.middleware.auth')

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
end

-- Rotas protegidas (registre o middleware antes de montar essas rotas
-- no app.lua, já que app:use() é sempre global):
--
--   app:use(auth.jwt())
--   app:get('/auth/profile', function(ctx) ... end)
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

## 📧 Email

`crescent.utils.mail` envia email via SMTP, construído sobre
`socket.smtp`/`ltn12`/`mime` (dependência LuaRocks: `luasocket`). As
credenciais padrão vêm do `.env` (`SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`,
`SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_FROM_NAME`).

```bash
# .env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app
SMTP_FROM=seu_email@gmail.com
SMTP_FROM_NAME="Minha Aplicação"
```

### Enviar Email

```lua
local mail = require('crescent.utils.mail')

-- Texto simples
local result, err = mail.send_text(
    "destinatario@example.com",
    "Bem-vindo!",
    "Obrigado por se cadastrar."
)

-- HTML (com fallback em texto opcional)
local result, err = mail.send_html(
    "destinatario@example.com",
    "Bem-vindo!",
    "<h1>Bem-vindo!</h1><p>Seu cadastro foi confirmado.</p>",
    "Bem-vindo! Seu cadastro foi confirmado."
)

-- Opções completas (to/cc/bcc aceitam string, array de strings, ou
-- array de {email=..., name=...})
local result, err = mail.send({
    to = { { email = "user@example.com", name = "Usuário" } },
    cc = "outro@example.com",
    subject = "Relatório mensal",
    html = "<h1>Relatório</h1>",
    reply_to = "suporte@example.com"
})

if not result then
    print("Falha ao enviar:", err)
end
```

### Template (etlua)

```lua
local mail = require('crescent.utils.mail')

-- Renderiza o .etlua com etlua.render, envia como HTML e gera
-- automaticamente uma versão em texto puro (strip de tags)
local result, err = mail.send_template(
    "destinatario@example.com",
    "Recuperação de senha",
    "views/emails/reset-password.etlua",
    { reset_link = "https://app.com/reset?token=abc123" }
)
```

### Instância customizada e verificação de conexão

```lua
local mail = require('crescent.utils.mail')

local custom_mailer = mail.create({
    server = "smtp.outro-provedor.com",
    port = 465,
    user = "outro@example.com",
    password = "..."
})

-- Testa conectividade TCP com o servidor SMTP (não envia email)
local ok, msg = mail.verify()
```

---

## 🌐 Variáveis de Ambiente

```lua
local env = require('crescent.utils.env')

-- Carregar .env (usado automaticamente por env.get() na primeira chamada)
env.load('.env')

-- Obter valores, com fallback opcional
local dbHost = env.get('DB_HOST', 'localhost')
local port = env.get('APP_PORT')
local isDev = env.get('APP_ENV') == 'development'

-- Limpar cache (útil em testes que trocam variáveis em runtime)
env.clear_cache()
```

> Não existe `env.has(...)` — para checar presença, compare com `nil`:
> `if env.get('API_KEY') then ... end`.

---

## 📨 Headers HTTP

`crescent.utils.headers` normaliza headers de requisição (não é um parser
de headers de resposta genérico).

```lua
local headers = require('crescent.utils.headers')

-- normalize(req) recebe o OBJETO de requisição inteiro (req.rawHeaders /
-- req.headers), não um nome de header — devolve uma tabela com todos os
-- headers em lowercase: { authorization = "...", ["content-type"] = "..." }
local normalized = headers.normalize(req)

-- Extrai o token de um header "Authorization: Bearer <token>" já normalizado
local token = headers.get_bearer(normalized)
```

> ⚠️ **`headers.is_safe_value()` está quebrado hoje** (mesma causa de
> `stringUtil.is_safe()`/`sanitize()`, ver seção "String Utilities" abaixo):
> o pattern `[\r\n\0]` inclui um byte nulo dentro de uma character class, o
> que lança `malformed pattern (missing ']')` em qualquer chamada neste
> Luvit/LuaJIT, independente do conteúdo testado. Bug de código, reportado
> aqui, não corrigido.

Na prática, você raramente chama `headers.normalize()` direto — o
`crescent.core.context` já expõe o resultado normalizado em `ctx.headers`,
e `ctx.getHeader(name)` / `ctx.getBearer()` fazem a leitura pra você:

```lua
local auth_header = ctx.getHeader("authorization")
local token = ctx.getBearer()
```

---

## 🛤️ Path Utilities

`crescent.utils.path` foi feito para paths de **rota HTTP**, não para
manipulação de paths de arquivo do sistema operacional (não existe
`dirname`/`basename`/`extname`).

```lua
local pathUtil = require('crescent.utils.path')

-- Junta dois segmentos de path (só 2 argumentos)
local fullPath = pathUtil.join('/api', 'users')
-- "/api/users"

-- Normaliza: colapsa "//" repetidos e garante "/" inicial
-- (NÃO resolve ".."/"." — isso é tratado por is_safe, não normalize)
local normalized = pathUtil.normalize('api//users')
-- "/api/users"

-- Valida se o path é seguro (sem ".." nem null byte) — usado
-- internamente pelo middleware de arquivos estáticos contra path traversal
local safe = pathUtil.is_safe('/../../etc/passwd')  -- false
local safe2 = pathUtil.is_safe('/css/app.css')       -- true

-- Compila um template de rota "/user/{id}" em pattern Lua + nomes de
-- parâmetros — usado internamente pelo roteador
local pattern, names = pathUtil.compile('/user/{id}')
-- pattern: "^/user/?([^/]*)$"; names: {"id"}
```

---

## 🔤 String Utilities

`crescent.utils.string` foca em segurança (sanitização/validação), não em
manipulação geral de strings — não existem `split`/`startsWith`/
`endsWith`/`upper`/`lower`/`titleCase`/`slugify`.

```lua
local stringUtil = require('crescent.utils.string')

-- Remove espaços do início/fim
local trimmed = stringUtil.trim('  hello  ')  -- "hello"

-- Escapa metacaracteres de pattern Lua (evita injeção de pattern em
-- gsub/match/find quando o texto vem de input externo)
local safe_pattern = stringUtil.escape_lua_pattern('1.99 (promo)')
-- "1%.99 %(promo%)"

-- Limita o tamanho (proteção contra payloads gigantes / DoS)
local limited = stringUtil.limit(long_string, 8192)  -- default 8192
```

Para split/case/slugify, use as primitivas nativas do Lua (`string.gmatch`,
`string.upper`/`lower`, `string.gsub`) diretamente — não há um wrapper do
Crescent pra isso hoje.

> ⚠️ **`is_safe()` e `sanitize()` estão quebrados hoje.** Ambos usam o
> pattern `[\0-\8\11-\12\14-\31\127]` (byte nulo como início de um range de
> character class) — testado neste Luvit/LuaJIT, isso lança
> `malformed pattern (missing ']')` em **qualquer** chamada, mesmo com
> entrada sem byte nulo (o erro é no parsing do pattern, não no conteúdo).
> É um bug no código-fonte (`crescent/utils/string.lua`), não um erro de
> documentação — reportado, não corrigido aqui. Enquanto não for corrigido,
> não use `is_safe()`/`sanitize()`; `escape_lua_pattern()` e `limit()`
> continuam funcionando normalmente.

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
    
    testStringEscapePattern = function()
        tests.assertEquals(stringUtil.escape_lua_pattern("1.99"), "1%.99")
    end,

    testStringLimit = function()
        tests.assertEquals(#stringUtil.limit(string.rep("a", 20), 5), 5)
        tests.assertEquals(stringUtil.limit("hello", 8192), "hello")
    end
    -- stringUtil.is_safe()/sanitize() não entram aqui: estão quebrados
    -- hoje (ver seção "String Utilities" acima), passariam pra sempre
    -- lançar erro em vez de rodar a asserção
}

tests.runSuite("Utility Tests", utilTests)
```

---

## 🎨 Templates e Views (etlua)

O Crescent inclui suporte a templates usando **etlua** (Embedded Lua), permitindo criar aplicações MVC.

### Sintaxe Básica

```html
<!-- Variáveis -->
<h1>Olá, <%= name %>!</h1>

<!-- Condicionais -->
<% if user.admin then %>
    <p>Você é admin</p>
<% end %>

<!-- Loops -->
<ul>
<% for i, item in ipairs(items) do %>
    <li><%= item.name %></li>
<% end %>
</ul>
```

### Renderizar Views no Controller

```lua
local function show_profile(ctx)
    local user = User:find(ctx.params.id)
    
    -- Renderiza view com dados
    return ctx.view("views/profile.etlua", {
        name = user.name,
        email = user.email,
        created_at = user.created_at
    })
end
```

### Renderizar Template Direto

```lua
local etlua = require("crescent.utils.etlua")

-- String
local html = etlua.render("Olá, <%= name %>!", { name = "João" })

-- Arquivo
local html, err = etlua.render_file("views/home.etlua", {
    title = "Home",
    users = users_list
})

if not html then
    print("Erro: " .. err)
end
```

### Tags Disponíveis

- `<% código %>` - Executa código Lua (sem output)
- `<%= variável %>` - Exibe valor (com escape HTML automático)
- `<%- variável %>` - Exibe valor (SEM escape HTML)
- `<% código -%>` - Remove quebra de linha após a tag

### Exemplo Completo

**Controller (src/users/controllers/users.lua):**
```lua
local User = require("src.users.models.users")

local function list(ctx)
    local users = User:all()
    
    return ctx.view("views/users/list.etlua", {
        users = users,
        total = #users
    })
end

local function show(ctx)
    local user = User:find(ctx.params.id)
    
    if not user then
        return ctx.error(404, "Usuário não encontrado")
    end
    
    return ctx.view("views/users/show.etlua", {
        name = user.name,
        email = user.email,
        role = user.role
    })
end

return {
    list = list,
    show = show
}
```

**View (views/users/list.etlua):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Lista de Usuários</title>
</head>
<body>
    <h1>Usuários (<%= total %>)</h1>
    
    <% if total > 0 then %>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nome</th>
                    <th>Email</th>
                </tr>
            </thead>
            <tbody>
                <% for i, user in ipairs(users) do %>
                <tr>
                    <td><%= user.id %></td>
                    <td><%= user.name %></td>
                    <td><%= user.email %></td>
                </tr>
                <% end %>
            </tbody>
        </table>
    <% else %>
        <p>Nenhum usuário encontrado.</p>
    <% end %>
</body>
</html>
```

### Passando Funções para Views

```lua
return ctx.view("views/dashboard.etlua", {
    users = users,
    format_date = function(timestamp)
        return os.date("%d/%m/%Y", timestamp)
    end
})
```

Usando na view:
```html
<p>Data: <%= format_date(os.time()) %></p>
```

### Tratamento de Erros

```lua
local etlua = require("crescent.utils.etlua")

local html, err = etlua.render_file("views/my_view.etlua", data)

if not html then
    print("Erro ao renderizar: " .. err)
    return ctx.html(500, "<h1>Erro ao carregar página</h1>")
end

return ctx.html(200, html)
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
2. **Use fallbacks**: `env.get('APP_PORT', 8080)`
3. **Valide valores críticos**: MySQL, API keys
4. **Diferentes arquivos por ambiente**: `.env.dev`, `.env.prod`

---

## 📖 Próximas Seções

- **[Database & ORM](/docs/database)** - Models, relações e migrations
- **[Core Concepts](/docs/core-concepts)** - Rotas, controllers e services
- **[Deployment](/docs/deployment)** - Deploy em produção
