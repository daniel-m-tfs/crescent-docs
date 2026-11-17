# Conceitos

## A aplicação

O `app.lua` cria a aplicação com `Crescent.new(config)`, registra middlewares e módulos e **retorna o `app`**. O Nginx executa esse arquivo **uma vez por worker** e, a cada requisição, chama `require("app"):run()`:

```nginx
location / {
    content_by_lua_block {
        require("app"):run()
    }
}
```

Consequências práticas:

- Código no topo de `app.lua` e dos módulos roda uma vez por worker, não por requisição. Não guarde estado de requisição em variáveis de módulo; use `ctx.state`.
- Em produção (`lua_code_cache on`) é preciso recarregar o Nginx para aplicar mudanças. Em desenvolvimento o `nginx.conf` usa `lua_code_cache off` e recarrega o código a cada requisição.
- O Nginx de produção constrói o app já no `init_by_lua_block`: um erro de configuração falha o start/reload em vez da primeira requisição.

Cada módulo expõe uma função `register(app)`:

```lua
-- src/hello/init.lua
local controller = require("src.hello.controllers.hello")

local Module = {}

function Module.register(app)
    app:get("/", controller.index, "hello.index")
end

return Module
```

## Configuração e ambiente

`Config.load()` carrega `config/<APP_ENV>.lua` (padrão `development`). Os arquivos de config leem variáveis com `crescent.env`:

```lua
-- config/production.lua
local Env = require("crescent.env")

return {
    environment = "production",
    debug = false,
    server = { host = "127.0.0.1", port = 8080, max_body_size = 5 * 1024 * 1024 },
    database = {
        host = Env.get("DB_HOST"),
        port = Env.number("DB_PORT", 3306),
        database = Env.get("DB_NAME"),
        user = Env.get("DB_USER"),
        password = Env.get("DB_PASSWORD"),
    },
}
```

| Função | Retorno |
| --- | --- |
| `Env.get(nome, padrão)` | string; ordem: variável do processo, depois `.env`, depois o padrão |
| `Env.number(nome, padrão)` | número (erro se o valor não for numérico) |
| `Env.boolean(nome, padrão)` | `true`/`false` a partir de `true`, `1`, `yes`, `false`, `0`, `no` |

> **Pegadinha do Nginx:** o Nginx limpa o ambiente dos workers. **Toda variável lida pela aplicação precisa de uma diretiva `env NOME;`** no `nginx.conf` e nos arquivos de `conf/`, senão `Env.get` não a enxerga (em produção, sem `.env`, ela simplesmente vem vazia). Os arquivos gerados já declaram `APP_*`, `DB_*`, `JWT_SECRET` e `SMTP_*`.

O `.env` é só conveniência local; em produção use variáveis de ambiente de verdade. A porta é definida pelo `listen` do `nginx.conf` (o `server.port` da config é apenas validado).

Outras chaves aceitas pela config da aplicação:

| Chave | Uso |
| --- | --- |
| `debug` | inclui detalhes internos nas respostas de erro e desativa o cache de templates |
| `database` | conexão MySQL; quando tem `database`, o app configura o banco e expõe `ctx.db` |
| `views_root` / `view_layout` | pasta dos templates (padrão `views`) e layout padrão |
| `error_handler` | função `(ctx, err)` para erros não tratados (veja [Erros](#erros)) |
| `logger` | instância de `crescent.logger` ou `function(level, message, fields)` |
| `secret_key` / `secret_key_fallbacks` | segredo de cookies assinados, sessões e CSRF (padrão: `APP_KEY`) |
| `upload_root` / `upload` | destino de `ctx:save_upload` e limites de upload |

## Rotas

```lua
app:get("/users", list_users)
app:post("/users", create_user)
app:put("/users/{id}", update_user)
app:patch("/users/{id}", patch_user)
app:delete("/users/{id}", delete_user)
```

| Padrão | Exemplo | `ctx.params` |
| --- | --- | --- |
| `/users/{id}` | `/users/42` | `{ id = "42" }` |
| `/posts/{slug?}` | `/posts` e `/posts/ola` | `slug` é `nil` quando ausente |
| `/files/{path*}` | `/files/a/b/c.txt` | `{ path = "a/b/c.txt" }` (só no último segmento) |

Parâmetros chegam sempre como **string**. Rotas estáticas têm prioridade sobre rotas com parâmetros, independentemente da ordem de registro.

Grupos e nomes:

```lua
app:group("/api/v1", function(api)
    api:get("/users/{id}", show_user, "users.show")   -- GET /api/v1/users/{id}
end)

app:route("users.show")   -- "/api/v1/users/{id}"
```

- `HEAD` usa a rota `GET` automaticamente.
- Caminho existente com outro método responde `405` com o header `Allow`; caminho inexistente responde `404` (`route_not_found`).
- `lua cli.lua routes` lista todas as rotas com método, caminho e nome.

## Controllers e o ctx

Um handler de rota é uma função que recebe o contexto da requisição (`ctx`) e responde. Nos módulos, os handlers ficam em `controllers/` e delegam as regras de negócio para `services/`:

```lua
app:get("/users/{id}", function(ctx)
    local user = User:find_or_fail(ctx.params.id)
    return ctx:json(200, { data = user:to_table() })
end)
```

### Dados da requisição

| Campo | Conteúdo |
| --- | --- |
| `ctx.params` | parâmetros da rota |
| `ctx.query` | query string (valores string; chave repetida vira lista) |
| `ctx.body` | JSON ou form decodificado em tabela; outros tipos ficam como string |
| `ctx.raw_body` | corpo original em texto |
| `ctx.files` | arquivos de um `multipart/form-data` (veja [Uploads](#uploads)) |
| `ctx:get_header("User-Agent")` | header (nome sem diferenciar maiúsculas) |
| `ctx:get_bearer()` | token de `Authorization: Bearer ...`, ou `nil` |
| `ctx:cookie("nome")` | cookie (veja [Cookies](#cookies)) |
| `ctx.method`, `ctx.path`, `ctx.route` | método, caminho e padrão da rota encontrada |
| `ctx.request_id`, `ctx.remote_addr` | id da requisição (também no header `X-Request-Id`) e IP do cliente |
| `ctx.state` | tabela livre para passar dados entre middleware e action |
| `ctx.db`, `ctx.config`, `ctx.app`, `ctx.debug` | banco, configuração, aplicação e modo debug |

Um corpo JSON inválido é recusado antes da action com `400 malformed_json`.

### Respostas

| Método | Resposta |
| --- | --- |
| `ctx:json(status, valor)` | JSON (`application/json; charset=utf-8`) |
| `ctx:text(status, texto)` | texto puro |
| `ctx:html(status, html)` | HTML |
| `ctx:view(nome, dados, opções)` | template etlua (veja [Views e layouts](#views-e-layouts)) |
| `ctx:redirect(url, status)` | redirecionamento (padrão `302`) |
| `ctx:no_content()` | `204` sem corpo |
| `ctx:error(status, mensagem, detalhes, código)` | erro JSON padronizado |
| `ctx:header(nome, valor)` | define um header da resposta (encadeável) |

Atalhos: retornar uma **tabela** envia `200` JSON e retornar uma **string** envia `200` texto. Uma action que não responde nem retorna nada gera `500 empty_response`.

```lua
app:get("/ping", function() return { pong = true } end)   -- 200 {"pong":true}
```

- `ctx:redirect` aceita só caminhos locais (`/...`); para outro domínio passe `{ allowed_hosts = { "exemplo.com" } }` como terceiro argumento.
- Para listas vazias em JSON use `json.array({})` (de `crescent.json`), senão uma tabela vazia vira `{}`.
- Models não viram JSON sozinhos: use `model:to_table()`.

## Middleware

Um middleware recebe `(ctx, next)`. Chame `next()` para continuar; para **bloquear**, responda sem chamar `next()`:

```lua
app:use(function(ctx, next)
    if ctx:get_header("X-Api-Key") ~= "segredo" then
        return ctx:error(401, "unauthorized", nil, "unauthorized")
    end
    ctx.state.client = "interno"
    return next()
end)
```

- Middlewares rodam na ordem de `app:use`, antes do roteamento, em todas as requisições.
- Código depois de `next()` roda depois da action. Para alterar headers da resposta nesse momento, use `ctx.res:before_flush(function(res) ... end)`, pois a resposta normalmente já foi enviada quando `next()` retorna.
- Para proteger uma rota só, envolva a action com `auth.protect` (aceita um middleware ou uma lista):

```lua
local auth = require("crescent.middleware.auth")

app:get("/admin", auth.protect({ auth.jwt(), require_admin }, admin_action))
```

`lua cli.lua make:middleware nome` gera o esqueleto em `src/middleware/nome.lua`. Os middlewares prontos (auth, CORS, rate limit, sessão, CSRF, headers de segurança, log) estão em [Segurança](/docs/security) e [Utilitários](/docs/utilities).

## Validação

`app:validated(schema, action, origem)` valida antes de chamar a action e responde `422 validation_failed` com os erros por campo. A origem padrão é `"body"`; use `"query"` para a query string.

```lua
app:post("/users", app:validated({
    name = { required = true, string = true, min_length = 3, max_length = 50 },
    email = { required = true, email = true },
    age = { number = true, min = 18 },
    role = { custom = function(v) return v == "admin" or v == "user", "role inválido" end },
}, function(ctx)
    return ctx:json(201, ctx.body)
end))
```

Resposta de erro:

```json
{
  "status": 422,
  "code": "validation_failed",
  "error": "validation failed",
  "details": { "name": [{ "code": "min_length", "message": "name must be at least 3 characters" }] }
}
```

| Regra | Valida |
| --- | --- |
| `required` | presente e diferente de `""` |
| `type = "string"` | tipo Lua exato (interrompe as demais regras do campo) |
| `string`, `number` | tipo do valor |
| `min_length`, `max_length`, `length` | tamanho de strings (em caracteres UTF-8) |
| `email`, `format` | e-mail simples; padrão Lua (`format = "^%d+$"`) |
| `min`, `max`, `range = { 1, 10 }` | limites de números |
| `custom` | `function(valor)` que retorna `true` ou `false, "mensagem"` |

Campos ausentes só falham com `required`. Valores de query string e de formulários são **strings**: `number = true` só passa para JSON; para query use `format` ou converta com `tonumber` na action.

Para validar manualmente: `local ok, errors = ctx:validate(schema, "query")`.

## Erros

Todo erro é um JSON com `status`, `code` (estável, para o cliente tratar) e `error` (mensagem); `details` é opcional:

```lua
return ctx:error(409, "e-mail já cadastrado", { field = "email" }, "email_taken")
-- 409 {"status":409,"code":"email_taken","error":"e-mail já cadastrado","details":{"field":"email"}}
```

Erros lançados (`error(...)`) dentro de controllers e middlewares:

- Viram `500 internal_error` e são registrados no log com o request id. O detalhe (mensagem e stack trace) só aparece na resposta com `debug = true`.
- Uma tabela com `status` 4xx vira essa resposta, sem log de erro. É assim que `Model:find_or_fail` produz `404 model_not_found`:

```lua
error({ status = 403, code = "no_access", public_message = "sem acesso" })
-- 403 {"status":403,"code":"no_access","error":"sem acesso"}
```

Para personalizar a resposta de erros 500, registre um handler (ele precisa responder):

```lua
app:on_error(function(ctx, err)
    return ctx:json(500, { error = "algo deu errado", request_id = ctx.request_id })
end)
```

Códigos que o próprio framework gera:

| Código | Status | Quando |
| --- | --- | --- |
| `route_not_found` | 404 | nenhuma rota para o caminho |
| `method_not_allowed` | 405 | caminho existe com outro método |
| `validation_failed` | 422 | `app:validated` |
| `model_not_found` | 404 | `find_or_fail` |
| `malformed_json`, `malformed_form` | 400 | corpo inválido |
| `invalid_redirect` | 400 | `ctx:redirect` para destino não permitido |
| `internal_error`, `empty_response` | 500 | erro não tratado; action sem resposta |
| `template_error` | 500 | falha ao renderizar um template |

Autenticação, CSRF, CORS, rate limit e uploads têm seus próprios códigos (`missing_credentials`, `csrf_invalid`, `rate_limited`...), listados em [Segurança](/docs/security).

## Views e layouts

Templates usam [etlua](https://github.com/leafo/etlua) e ficam em `views/`. O nome inclui a extensão `.etlua`:

```lua
app:get("/", function(ctx)
    return ctx:view("hello/index.etlua", { title = "Início" }, { layout = "layout.etlua" })
end)
```

```html
<!-- views/hello/index.etlua -->
<h1><%= title %></h1>
<ul>
  <% for _, item in ipairs(items or {}) do %>
    <li><%= item %></li>
  <% end %>
</ul>
```

```html
<!-- views/layout.etlua -->
<!doctype html>
<html lang="pt-BR">
<head><title><%= title or "Crescent" %></title></head>
<body><%- content %></body>
</html>
```

- `<%= valor %>` escapa HTML; `<%- valor %>` imprime sem escapar (use só com HTML confiável, como `content` e `csrf_field()`).
- O layout recebe a página pronta em `content` e os mesmos dados da página.
- Opções: `status` (padrão `200`) e `layout`. Defina `view_layout = "layout.etlua"` na config para ter um layout padrão; `layout = false` desliga em uma página.
- Helpers globais: `app.view_renderer:helper("upper", function(s) return s:upper() end)`.
- Com o middleware de sessão ativo, todo template recebe `csrf_token()` e `csrf_field()`.
- Templates ficam em cache quando `debug = false`.
