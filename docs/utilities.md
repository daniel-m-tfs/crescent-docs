# Utilitários

## Cliente HTTP

`crescent.http_client` faz requisições de saída sem bloquear o worker (sobre `lua-resty-http`):

```lua
local HttpClient = require("crescent.http_client")

local api = HttpClient.new({
    base_url = "https://api.example.com/v1",
    timeout = 5,                                   -- segundos (padrão 30)
    headers = { Authorization = "Bearer " .. token },
})

app:get("/repos", function(ctx)
    local res, err = api:get("/repos", { params = { page = 2 } })
    if not res then
        return ctx:error(502, "upstream failed", ctx.debug and err.message or nil, "upstream_error")
    end
    return ctx:json(200, res.data)
end)
```

- Métodos: `get(url, config)`, `delete`, `head`, `options`, e `post(url, dados, config)`, `put`, `patch`.
- Uma tabela em `dados` é enviada como JSON; uma string vai como está.
- A resposta é `{ status, headers, body, data }`; `data` é o JSON já decodificado (ou o corpo bruto).
- Falhas de rede e status `>= 400` retornam `nil, err`, com `err.message` e, quando houve resposta, `err.status` e `err.data`.
- TLS é verificado por padrão, redirecionamentos não são seguidos e respostas acima de 10 MiB são abortadas (`max_response_size`).
- Para chamadas avulsas: `HttpClient.get(url)`.

> O Nginx resolve DNS e verifica certificados para o Lua: os `nginx.conf` gerados já trazem `resolver` e `lua_ssl_trusted_certificate`. Sem eles, nomes não resolvem e conexões HTTPS falham. O cliente funciona em controllers, middlewares e timers, mas não em `init_by_lua`.

## E-mail

`crescent.mail` envia por SMTP (com STARTTLS) sobre `lua-resty-mail`. Os dados do servidor vêm das variáveis `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` e `SMTP_FROM_NAME`, ou podem ser passados em `Mail.new({ server, port, user, password, from, from_name })`:

```lua
local Mail = require("crescent.mail")

local mailer = Mail.new()

local ok, err = mailer:send({
    to = { "ada@example.com", { email = "grace@example.com", name = "Grace" } },
    subject = "Bem-vinda",
    text = "Olá!",
    html = "<p>Olá!</p>",
})
if not ok then ctx.state.log:error("falha no e-mail", { error = err }) end
```

- Também aceita `cc`, `bcc` e `reply_to`.
- Atalhos: `send_text(para, assunto, texto)`, `send_html(para, assunto, html)` e `send_template(para, assunto, "emails/welcome.etlua", dados)`, que renderiza um template de `views/`.
- Porta 465 usa TLS direto; as demais usam STARTTLS.
- Envie fora do caminho crítico quando possível: o envio espera a resposta do servidor SMTP.

## Logs

`crescent.logger` grava uma linha JSON por entrada no error log do Nginx (no Docker, em stderr). Campos sensíveis são mascarados automaticamente:

```lua
local Logger = require("crescent.logger")

local log = Logger.new({ level = "info", fields = { service = "api" } })
log:info("login", { user_id = 7, password = "x" })
-- {"level":"info","msg":"login","service":"api","user_id":7,"password":"[REDACTED]"}

log:with({ request_id = ctx.request_id }):warn("cota excedida")
```

- Níveis: `debug`, `info`, `warn`, `error`; entradas abaixo de `level` são ignoradas.
- Mascarados (por substring no nome do campo): `password`, `passwd`, `secret`, `token`, `authorization`, `cookie`, `api_key`, `credit_card`, `card_number`, `cvv`, `private_key`. Acrescente outros com `Logger.new({ redact = { "cpf" } })`.
- `Logger.redact(tabela, { "cpf" })` devolve uma cópia mascarada.

### Log por requisição

O `app.lua` gerado registra `request_log`, que grava uma entrada por requisição com método, caminho, rota, status, duração, IP, `user_id` (de `ctx.state.user`) e request id. Status 5xx saem como `error` e 4xx como `warn`.

```lua
app:use(Crescent.middleware.request_log.create({
    skip = function(ctx) return ctx.path == "/health" or ctx.path == "/ready" end,
}))

-- nos controllers, um logger já com o request id:
ctx.state.log:info("pedido criado", { order_id = order.id })
```

Todo erro 500 também é registrado pela aplicação com request id, método e caminho. Para usar seu próprio logger nesses registros: `Crescent.new({ logger = Logger.new({ level = "warn" }) })`.

## JSON

`crescent.json` envolve o `cjson` com a política do framework:

```lua
local json = require("crescent.json")

json.encode({ ok = true })            -- '{"ok":true}'
json.decode('{"items":[]}')           -- items continua lista ao reenviar
json.array({})                        -- força [] em vez de {}
```

Tabelas vazias viram `{}` em JSON. Para listas que podem estar vazias na resposta, use `json.array(lista)`. Barras não são escapadas (`"/a"` em vez de `"\/a"`).

## Health e readiness

`crescent.health` registra dois endpoints (o projeto gerado já faz isso em `src/health`):

```lua
require("crescent.health").register(app, {
    service = "api",
    checks = {
        database = require("crescent.health").checks.database,
        cache = function(ctx) return redis_ping() end,   -- true, ou nil e erro
    },
})
```

| Endpoint | Resposta |
| --- | --- |
| `GET /health` | `200` enquanto o worker responde; não consulta dependências |
| `GET /ready` | `200` se todos os checks passam, `503` caso contrário, com status e duração de cada check |

Sem `checks`, `/ready` verifica o banco (`SELECT 1`) quando há um configurado. Mensagens de erro dos checks só aparecem na resposta com `debug = true`; sempre vão para o log. Use `/health` para reiniciar o processo e `/ready` para o balanceador decidir se envia tráfego.
