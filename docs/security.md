# Segurança

## Autenticação

`crescent.middleware.auth` traz middlewares para JWT, Bearer, Basic e API key. Em caso de sucesso eles colocam o usuário em `ctx.state.user`; em caso de falha respondem `401` sem chamar a action.

```lua
local auth = require("crescent.middleware.auth")

-- uma rota
app:get("/me", auth.protect(auth.jwt(), function(ctx)
    return ctx:json(200, ctx.state.user)
end))

-- todas as rotas registradas depois
app:use(auth.jwt())
```

`auth.jwt()` lê o segredo de `JWT_SECRET` (mínimo de 32 bytes; gere com `openssl rand -base64 48`). Sem ele, o app falha ao iniciar.

| Middleware | Uso |
| --- | --- |
| `auth.jwt(opções)` | JWT de acesso no header `Authorization: Bearer`; define também `ctx.state.jwt` (payload) |
| `auth.bearer(fn)` | token opaco; `fn(token, ctx)` retorna `true, usuário` ou `false, "mensagem"` |
| `auth.basic(fn, { realm = "Admin" })` | HTTP Basic; `fn(usuário, senha, ctx)` |
| `auth.api_key("X-Api-Key", fn)` | chave em um header; `fn(chave, ctx)` |
| `auth.protect(middleware, action)` | aplica um middleware (ou uma lista) a uma action |

Opções de `auth.jwt`: `secret`, `issuer`, `audience`, `algorithms` (padrão `{ "HS256" }`), `leeway`, `optional = true` (não bloqueia; só preenche o usuário se o token for válido) e `get_user`:

```lua
app:use(auth.jwt({
    get_user = function(payload, ctx)
        return User:find(payload.user_id)   -- nil → 401
    end,
}))
```

API key e Basic:

```lua
app:get("/internal", auth.protect(auth.api_key("X-Api-Key", function(key, ctx)
    if auth.secure_compare(key, os.getenv("INTERNAL_KEY") or "") then
        return true, { name = "servico-interno" }
    end
    return false, "invalid api key"
end), internal_action))
```

Use `auth.secure_compare(a, b)` para comparar segredos (tempo constante).

## Login com JWT

```lua
local auth = require("crescent.middleware.auth")
local password = require("crescent.security.password")
local User = require("src.users.models.user")

app:post("/auth/login", app:validated({
    email = { required = true, email = true },
    password = { required = true },
}, function(ctx)
    local user = User:where("email", ctx.body.email):first()
    if not user or not password.verify(ctx.body.password, user.password) then
        return ctx:error(401, "invalid credentials", nil, "invalid_credentials")
    end
    return auth.generate_token_pair(user)
    -- { access_token, refresh_token, token_type = "Bearer", expires_in, refresh_expires_in }
end))

app:post("/auth/refresh", function(ctx)
    local ok, payload = auth.verify_refresh_token(ctx.body.refresh_token)
    if not ok then return ctx:error(401, "invalid token", nil, "invalid_token") end
    auth.revoke_token(payload)   -- o refresh token antigo deixa de valer
    return auth.generate_token_pair(payload.user_id)
end)

app:post("/auth/logout", auth.protect(auth.jwt(), function(ctx)
    auth.revoke_token(ctx.state.jwt)
    return ctx:no_content()
end))
```

- O access token dura 15 minutos e o refresh token 30 dias (`access_expires_in` e `refresh_expires_in`, em segundos, mudam isso). O payload leva `user_id`, `name` e `email`.
- `auth.jwt()` recusa refresh tokens; `verify_refresh_token` aceita só refresh tokens.
- Tokens revogados ficam no `lua_shared_dict crescent_jwt` (compartilhado entre workers, já declarado no `nginx.conf`) até expirarem. O dict é perdido ao reiniciar o Nginx e não é compartilhado entre servidores.

Para assinar e verificar diretamente, use `crescent.security.jwt`:

```lua
local jwt = require("crescent.security.jwt")

local token = jwt.sign({ user_id = 1 }, secret, { expires_in = 900, issuer = "api" })
local ok, payload_or_message, code = jwt.verify(token, secret, { issuer = "api" })
```

Algoritmos HS256/HS384/HS512; o algoritmo é fixado por quem verifica (`algorithms`), nunca pelo token, e `none` nunca é aceito.

## Senhas

```lua
local password = require("crescent.security.password")

local hash = password.hash("s3cr3t")          -- "600000$<salt>$<hash>"
password.verify("s3cr3t", hash)               -- true
password.needs_rehash(hash)                   -- true se as iterações mudaram
```

PBKDF2-HMAC-SHA256 com 600.000 iterações (recomendação OWASP), executado pelo OpenSSL. Cada hash leva dezenas de milissegundos e ocupa o worker: aplique [rate limit](#rate-limit) no login. `PASSWORD_HASH_ITERATIONS` ajusta o padrão. Hashes gerados pelo Crescent 1.x continuam válidos.

## CORS

Registre o CORS **antes** da autenticação, com `app:use`, para que o preflight (`OPTIONS`) seja respondido antes de exigir credenciais:

```lua
local cors = require("crescent.middleware.cors")

app:use(cors.create({
    origins = { "https://app.example.com" },   -- ou "*", ou function(origin, ctx)
    methods = { "GET", "POST", "PUT", "DELETE" },
    allowed_headers = { "Content-Type", "Authorization" },
    credentials = true,
    max_age = 600,
}))
```

- O preflight é respondido com `204` pelo próprio middleware; não crie rotas `OPTIONS`.
- `cors.strict({ "https://app.example.com" })` liga credenciais, cache de preflight de 24 h e responde `403` a outras origens.
- `credentials = true` com `origins = "*"` é recusado.

## Headers de segurança

```lua
app:use(Crescent.middleware.security_headers.create({
    hsts = true,                                         -- só se o site for 100% HTTPS
    csp = "default-src 'self'; frame-ancestors 'none'",
}))
```

Sem opções, envia `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e `Referrer-Policy: strict-origin-when-cross-origin` (o `app.lua` gerado já registra esse middleware). Outras opções: `frame_options`, `referrer_policy`, `permissions_policy`, `cross_origin_opener_policy` e `headers` (extras; `false` remove um header).

## Rate limit

```lua
local rate_limit = require("crescent.middleware.rate_limit")

app:use(rate_limit.create({ limit = 100, window = 60 }))   -- 100 req/min por IP

app:post("/auth/login", auth.protect(
    rate_limit.create({ limit = 5, window = 60, prefix = "rl:login:" }), login))
```

- Janela fixa no `lua_shared_dict crescent_limits`, compartilhada entre workers.
- Acima do limite: `429 rate_limited` com `Retry-After`. Toda resposta traz `X-RateLimit-Limit`, `X-RateLimit-Remaining` e `X-RateLimit-Reset`.
- Use um `prefix` diferente para cada limitador.
- A chave padrão é o IP (`ctx.remote_addr`). Atrás de proxy, configure o `realip` do Nginx (veja [Deploy](/docs/deployment)); nunca use o `X-Forwarded-For` cru como chave. `key = function(ctx) ... end` personaliza; retornar `nil` isenta a requisição.

## Cookies

```lua
ctx:set_cookie("theme", "dark", { max_age = 3600 })
ctx:cookie("theme")                         -- "dark"
ctx:clear_cookie("theme")                   -- mesmo path/domain usados no set

ctx:set_cookie("uid", tostring(user.id), { signed = true })
ctx:signed_cookie("uid")                    -- nil se ausente ou adulterado
```

| Opção | Padrão |
| --- | --- |
| `path` | `"/"` |
| `max_age` / `expires` | cookie de sessão |
| `http_only` | `true` |
| `secure` | `true` fora de `debug` |
| `same_site` | `"Lax"` (`"Strict"`, `"Lax"` ou `"None"`; `None` exige `secure`) |
| `domain`, `signed` | — |

Cookies assinados, sessões e CSRF usam o segredo `APP_KEY` (ou `secret_key` na config), com no mínimo 32 caracteres: `openssl rand -base64 48`. Para trocar a chave sem invalidar tudo, mova a antiga para `secret_key_fallbacks`.

## Sessões

```lua
local session = require("crescent.middleware.session")

app:use(session.create())   -- cookie criptografado (AES-256-GCM), 24 h, expira após 1 h sem uso
```

```lua
app:post("/login", function(ctx)
    local user = authenticate(ctx.body.email, ctx.body.password)
    if not user then
        ctx.session:flash("error", "credenciais inválidas")
        return ctx:redirect("/login")
    end
    ctx.session:regenerate()              -- sempre após login (evita session fixation)
    ctx.session:set("user_id", user.id)
    return ctx:redirect("/")
end)

app:post("/logout", function(ctx)
    ctx.session:destroy()
    return ctx:redirect("/")
end)
```

| Método | Efeito |
| --- | --- |
| `get(k)`, `set(k, v)`, `delete(k)` | valores (serializáveis em JSON) |
| `flash(k, v)` / `get_flash(k)` | valor disponível só na próxima requisição |
| `regenerate()` | nova sessão com os mesmos dados |
| `destroy()` | apaga a sessão e expira o cookie |
| `clear()`, `is_new()` | limpa os valores; sessão criada nesta requisição |

| Opção | Padrão | |
| --- | --- | --- |
| `store` | `"cookie"` | `"shared"` guarda os dados no `lua_shared_dict crescent_sessions` e o cookie leva só um id |
| `name` | `"crescent_session"` | nome do cookie |
| `max_age` / `idle_timeout` | `86400` / `3600` | segundos; `false` desativa |
| `cookie` | `{ path = "/", same_site = "Lax", http_only = true }` | opções do cookie |

O store `cookie` não guarda estado no servidor, mas tem limite de 4 KB (guarde ids, não objetos) e um cookie copiado continua válido até expirar. O store `shared` invalida a sessão de verdade no `destroy`, porém é perdido ao reiniciar o Nginx e não é compartilhado entre servidores.

## CSRF

Formulários com login por cookie precisam de proteção CSRF. Registre o middleware **depois** da sessão:

```lua
local session = require("crescent.middleware.session")
local csrf = require("crescent.middleware.csrf")

app:use(session.create())
app:use(csrf.create({
    skip = function(ctx) return ctx:get_bearer() ~= nil end,   -- APIs com bearer token
}))
```

Nos templates, inclua o campo com `<%-` (sem escape, pois é HTML):

```html
<form method="post" action="/posts">
  <%- csrf_field() %>
  <input name="title">
  <button>Salvar</button>
</form>

<meta name="csrf-token" content="<%= csrf_token() %>">
```

Requisições `POST`, `PUT`, `PATCH` e `DELETE` precisam enviar o token no campo `_csrf` ou no header `X-CSRF-Token` (para AJAX, leia a meta tag). Sem token válido: `403 csrf_invalid`.

- **Protegido contra BREACH:** o segredo de 256 bits fica na sessão e nunca aparece numa resposta. `csrf_token()` devolve o segredo mascarado com uma máscara aleatória nova a cada requisição, então páginas comprimidas não repetem os bytes do segredo. Qualquer token mascarado do segredo atual é aceito (várias abas funcionam).
- `ctx.session:regenerate()` no login troca o segredo: tokens obtidos antes do login deixam de valer.

## Uploads

Requisições `multipart/form-data` são lidas em streaming: os campos de texto vão para `ctx.body` e os arquivos para `ctx.files`, gravados em arquivos temporários.

```lua
app:post("/avatar", function(ctx)
    local file = ctx.files.avatar   -- { filename, content_type, size, path, field }
    if not file then return ctx:error(422, "avatar obrigatório", nil, "avatar_required") end
    if file.content_type ~= "image/png" then
        return ctx:error(422, "apenas PNG", nil, "invalid_type")
    end
    local path, err = ctx:save_upload(file, "avatars/" .. ctx.state.user.id .. ".png", { overwrite = true })
    if not path then return ctx:error(500, "falha ao salvar", nil, "upload_failed") end
    return ctx:json(201, { path = path })
end)
```

Configure o destino e os limites na config da aplicação:

```lua
upload_root = "storage",              -- única pasta em que save_upload grava (relativa ao projeto)
upload = {
    max_file_size = 10 * 1024 * 1024,
    max_files = 10,
    max_total_size = 50 * 1024 * 1024,
},
```

- Temporários não salvos com `ctx:save_upload` são apagados ao fim da requisição.
- `filename` e `content_type` vêm do cliente: valide o conteúdo e gere você o nome final. Caminhos com `..` ou fora de `upload_root` são recusados.
- Ajuste também `client_max_body_size` no `nginx.conf`.

| Situação | Status | Código |
| --- | --- | --- |
| arquivo, campo ou total acima do limite | 413 | `upload_too_large` |
| arquivos ou campos demais | 413 | `too_many_files`, `too_many_fields` |
| multipart inválido | 400 | `malformed_multipart` |

## Códigos de erro

| Código | Status | Origem |
| --- | --- | --- |
| `missing_credentials` | 401 | header de autenticação ausente |
| `invalid_token`, `invalid_credentials` | 401 | token ou credenciais inválidos |
| `token_expired`, `token_revoked` | 401 | JWT expirado ou revogado |
| `csrf_invalid` | 403 | token CSRF ausente ou errado |
| `cors_origin_not_allowed` | 403 | origem fora da lista (preflight ou `cors.strict`) |
| `rate_limited` | 429 | limite excedido |

Referência completa: [security.md](https://github.com/daniel-m-tfs/crescent-framework/blob/main/docs/security.md) e [web.md](https://github.com/daniel-m-tfs/crescent-framework/blob/main/docs/web.md) do framework.
