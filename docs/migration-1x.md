# Migrando do 1.x

## O que mudou

O Crescent 2.0 é uma reescrita: troca o **Luvit** pelo **OpenResty** (Nginx + LuaJIT). O Nginx passa a cuidar do servidor HTTP, dos workers e dos arquivos estáticos, e o banco continua sendo MySQL. A organização em módulos (`src/<módulo>` com controllers, services, models e rotas) continua a mesma, mas a API mudou em pontos que quebram código existente.

A forma mais simples de migrar é criar um projeto novo a partir do [starter](https://github.com/daniel-m-tfs/crescent-starter) e trazer seus módulos, ajustando-os com a lista abaixo.

## Mudanças que quebram código

| 1.x (Luvit) | 2.0 (OpenResty) |
| --- | --- |
| `ctx.json(200, dados)`, `ctx.text`, `ctx.redirect`... | `ctx:json(200, dados)`, `ctx:text`, `ctx:redirect`... (dois-pontos em todo o contexto) |
| `app:listen(8080)` e `luvit app.lua` | `app.lua` retorna o `app`; o Nginx o executa (`bin/crescent server start`); a porta fica no `listen` do `nginx.conf` |
| middleware interrompe com `return false` | middleware responde sem chamar `next()`: `return ctx:error(401, ...)` |
| middleware só global | também por rota: `auth.protect(middleware, action)` |
| `jwt.sign(..., { expiresIn = 900, notBefore = 0 })` | opções em snake_case: `expires_in`, `not_before` |
| `require("crescent.utils.jwt")` | `require("crescent.security.jwt")` |
| `require("crescent.utils.hash")`, `hash.encrypt` | `require("crescent.security.password")`, `password.hash` / `password.verify` |
| `require("crescent.utils.http")` | `require("crescent.http_client")` |
| `require("crescent.utils.mail")` | `require("crescent.mail")` |
| `require("crescent.utils.env")` | `require("crescent.env")` (e `env NOME;` no `nginx.conf`) |
| `require("crescent.database.model")` | `require("crescent.model")` |
| `Model:where(...):get()` devolvia linhas | devolve instâncias do model (use `to_table()` para JSON) |
| middleware `static` | arquivos em `public/`, servidos pelo Nginx em `/public/` |
| middleware `logger` | `Crescent.middleware.request_log` |
| `luvit crescent-cli.lua <comando>` | `lua cli.lua <comando>` (ou `bin/crescent <comando>`) |

## O que continua valendo

- **Hashes de senha** do 1.x (`iteracoes$salt$hash`) são verificados normalmente por `password.verify`. Use `password.needs_rehash` no login para atualizá-los para 600.000 iterações aos poucos.
- Nomes camelCase do ORM (`findOrFail`, `orderBy`, `whereIn`, `toTable`...) continuam disponíveis como apelidos, mas a documentação usa snake_case.
- `crescent.utils.tests` e o formato `tests/test-*.lua` continuam; rode com `bin/crescent test`.
- O banco é o mesmo MySQL: suas tabelas continuam servindo. Confira as migrations antigas contra o formato novo (`up`/`down` retornando SQL; veja [Migrations](#migrations)).

## Pontos de atenção

- **Estado global:** o `app.lua` roda uma vez por worker e vários workers atendem em paralelo. Estado em variáveis de módulo não é compartilhado entre workers; use o banco ou `ngx.shared`.
- **Variáveis de ambiente:** declare cada uma com `env NOME;` no `nginx.conf`, senão os workers não as enxergam.
- **I/O:** use as bibliotecas do OpenResty (cosockets): `crescent.http_client`, `crescent.mail`, `lua-resty-*`. Módulos do Luvit (`coro-http`, `fs` assíncrono...) não funcionam.
- **Erros:** os erros gerados pelo framework (404, 405, validação, autenticação...) seguem o formato `{ status, code, error, details }`; ajuste clientes que dependiam das respostas antigas.
