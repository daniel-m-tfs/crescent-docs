# Começando

## O que é o Crescent

Crescent é um framework web em Lua que roda sobre o **OpenResty** (Nginx + LuaJIT) e usa **MySQL**. O Nginx cuida do HTTP (TLS, workers, keep-alive, limites, arquivos estáticos); o Crescent cuida de rotas, middleware, validação, ORM, migrations, templates, segurança e CLI.

Esta documentação é da versão **2.0**. Vindo do Crescent 1.x (Luvit)? Veja [Migrando do 1.x](/docs/migration-1x).

### Requisitos

| Com Docker | Sem Docker |
| --- | --- |
| Docker com Compose | OpenResty (inclui `resty`, `lua-resty-mysql`, `lua-resty-openssl`) |
| — | LuaRocks (para instalar `etlua`, `lua-resty-http`, `lua-resty-mail`) |
| — | MySQL 8 ou MariaDB |

## Criando um projeto

O jeito mais rápido é partir do template [crescent-starter](https://github.com/daniel-m-tfs/crescent-starter): ele já traz um hello world, Docker, MySQL e a CLI.

```bash
git clone https://github.com/daniel-m-tfs/crescent-starter.git meu-app
cd meu-app
```

Se você tem o repositório do framework, `bin/crescent new meu-app` gera o mesmo projeto.

### Com Docker (recomendado)

```bash
cp .env.example .env
docker compose up --build
```

Pronto:

- [http://127.0.0.1:8080](http://127.0.0.1:8080) — página hello world
- `/api/hello?name=Ada` — exemplo JSON com validação
- `/health` e `/ready` — liveness e readiness (verifica o banco)

O código fica montado no container com recarga automática (edite e recarregue a página) e as migrations pendentes rodam ao subir. Rode a CLI dentro do container:

```bash
docker compose exec app bin/crescent routes
```

### Sem Docker

```bash
./deps.sh                      # instala as dependências Lua em ./lua_modules
cp .env.example .env           # ajuste DB_* para o seu MySQL
./bin/crescent server start    # http://127.0.0.1:8080
curl http://127.0.0.1:8080/health
```

No Linux, aponte o `deps.sh` para o LuaJIT do OpenResty: `OPENRESTY_LUAJIT=/usr/local/openresty/luajit ./deps.sh` (o padrão é o caminho do Homebrew no macOS).

`./bin/crescent server stop` para o servidor. Em desenvolvimento o `nginx.conf` usa `lua_code_cache off`, então alterações no código valem na próxima requisição.

> **Atenção:** o servidor lê o `.env`, mas a CLI (que roda no `resty`) **não**. Antes de `db:*` e `routes`, exporte as variáveis no shell: `set -a; . ./.env; set +a`. No Docker isso já é feito pelo `env_file`.

## Estrutura do projeto

```
app.lua            monta a aplicação: middlewares + módulos
config/            configuração por ambiente (development.lua, production.lua, test.lua)
src/<módulo>/      init.lua (register), actions/, models/, services/, routes/
views/             templates etlua (layout.etlua + páginas)
public/            arquivos estáticos, servidos pelo Nginx em /public/
migrations/        bin/crescent make:migration
seeds/             bin/crescent make:seeder
tests/             bin/crescent test
crescent/  cli/    o framework, versionado junto com o projeto
nginx.conf         Nginx de desenvolvimento local
conf/              Nginx de produção e dos containers
Dockerfile  docker-compose.yml  docker/
```

O `app.lua` gerado:

```lua
local Crescent = require("crescent")
local Config = require("crescent.config")

local app = Crescent.new(Config.load())

app:use(Crescent.middleware.security_headers.create())
app:use(Crescent.middleware.request_log.create({
    skip = function(ctx) return ctx.path == "/health" or ctx.path == "/ready" end,
}))

require("src.health").register(app)
require("src.hello").register(app)

return app
```

## Primeiro módulo

Gere um CRUD completo (model, service, actions, rotas, teste e migration):

```bash
bin/crescent make:module Product
```

Registre o módulo no `app.lua`:

```lua
require("src.product").register(app)
```

Crie a tabela (com Docker: `docker compose exec app bin/crescent db:migrate`):

```bash
bin/crescent db:migrate
```

E teste:

```bash
curl -X POST http://127.0.0.1:8080/products \
  -H 'Content-Type: application/json' -d '{"name":"Teclado"}'
# 201 {"data":{"id":1,"name":"Teclado","created_at":"...","updated_at":"..."}}

curl http://127.0.0.1:8080/products
# {"data":[...],"meta":{"page":1,"per_page":15,"total":1,"last_page":1,"from":1,"to":1}}

curl http://127.0.0.1:8080/products/1
curl -X PUT http://127.0.0.1:8080/products/1 \
  -H 'Content-Type: application/json' -d '{"name":"Teclado mecânico"}'
curl -X DELETE http://127.0.0.1:8080/products/1    # 204
```

Um `POST` sem `name` responde `422` com os erros por campo; um id inexistente responde `404`.

| Método | Caminho | Nome da rota |
| --- | --- | --- |
| GET | `/products` | `products.index` |
| GET | `/products/{id}` | `products.show` |
| POST | `/products` | `products.store` |
| PUT | `/products/{id}` | `products.update` |
| DELETE | `/products/{id}` | `products.destroy` |

## Próximos passos

- [Conceitos](/docs/core-concepts) — rotas, `ctx`, middleware, validação, erros e views.
- [Banco de dados](/docs/database) — models, relações, query builder e migrations.
- [Segurança](/docs/security) — JWT, sessões, CSRF, CORS e rate limit.
- [CLI](/docs/cli) — todos os comandos do `bin/crescent`.
- [Deploy](/docs/deployment) — imagem Docker e Nginx de produção.
