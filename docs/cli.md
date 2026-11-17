# CLI

## Usando o bin/crescent

A CLI vem dentro do projeto e roda no mesmo LuaJIT do OpenResty que atende as requisições (via `resty`):

```bash
bin/crescent <comando> [argumentos]
bin/crescent help
```

No Docker, rode dentro do container: `docker compose exec app bin/crescent <comando>`.

> **Sem Docker:** a CLI não lê o `.env` (só o servidor lê). Exporte as variáveis antes dos comandos que acessam o banco ou carregam o app (`db:*`, `routes`): `set -a; . ./.env; set +a`.

| Variável | Uso |
| --- | --- |
| `RESTY_BIN` | caminho do `resty`, se não estiver em um local padrão |
| `OPENRESTY_BIN` | caminho do `openresty`, usado por `server` |
| `APP_ENV` | ambiente carregado (`config/<APP_ENV>.lua`) |

Códigos de saída: `0` sucesso, `1` falha, `2` comando desconhecido.

## Servidor e rotas

| Comando | Descrição |
| --- | --- |
| `server start` | inicia o OpenResty com o `nginx.conf` do projeto (porta 8080) |
| `server stop` | para de forma graciosa |
| `server reload` | recarrega configuração e código |
| `server status` | mostra se está rodando e o pid |
| `routes` | lista as rotas: método, caminho e nome |

Opções de `server`: `--conf <arquivo>` escolhe outra configuração do Nginx e `--env <nome>` define o `APP_ENV`:

```bash
bin/crescent server start --conf conf/nginx.production.conf --env production
```

Erros de inicialização vão para `logs/error.log`.

## Geradores

Os geradores **nunca sobrescrevem** arquivos. `BlogPost` e `blog-post` viram `blog_post` em nomes de arquivo e `BlogPost` no código. Quando o módulo é omitido, ele recebe o próprio nome.

| Comando | Cria |
| --- | --- |
| `make:module <nome>` | módulo CRUD completo em `src/<nome>/`, teste e migration (veja abaixo) |
| `make:action <nome> [módulo]` | `src/<módulo>/actions/<nome>.lua` |
| `make:service <nome> [módulo]` | `src/<módulo>/services/<nome>.lua` |
| `make:model <nome> [módulo]` | `src/<módulo>/models/<nome>.lua` |
| `make:routes <nome> [módulo]` | `src/<módulo>/routes/<nome>.lua` |
| `make:middleware <nome> [módulo]` | `src/middleware/<nome>.lua` (ou dentro do módulo) |
| `make:test <nome>` | `tests/test-<nome>.lua` |
| `make:migration <nome>` | `migrations/AAAAMMDDHHMMSS_<nome>.lua` |
| `make:seeder <nome>` | `seeds/<nome>.lua` |
| `new <nome>` | novo projeto em `./<nome>` (a partir do repositório do framework) |

Nomes começam com letra e usam letras, números, `_` ou `-` (migrations e seeders: só letras, números e `_`).

### make:module

```bash
bin/crescent make:module Product
```

```
src/product/init.lua              register(app): registra as rotas em /products
src/product/models/product.lua    Model (tabela products, campo name)
src/product/services/product.lua  regras de negócio (page, find, create, update, delete)
src/product/actions/product.lua   index, show, store, update, destroy + schema de validação
src/product/routes/product.lua    rotas nomeadas products.*
tests/test-product-module.lua
migrations/<data>_create_products_table.lua
```

Depois, registre `require("src.product").register(app)` no `app.lua` e rode `bin/crescent db:migrate`. As rotas geradas estão em [Primeiro módulo](#primeiro-módulo).

## Banco de dados

| Comando | Alias | Descrição |
| --- | --- | --- |
| `db:migrate` | `migrate` | aplica as migrations pendentes |
| `db:rollback` | `migrate:rollback` | desfaz o último lote de migrations |
| `db:status` | `migrate:status` | lista migrations (`ran`, `pending` ou `missing`) e lote |
| `db:seed [nome]` | — | roda todos os seeders, ou só um |

Os comandos usam `config.database` do ambiente atual (`APP_ENV`). Detalhes em [Migrations](#migrations) e [Seeders](#seeders).

## Testes

```bash
bin/crescent test            # todos os arquivos tests/test*.lua
bin/crescent test product    # só os que contêm "product" no nome
./test.sh                    # atalho do projeto
```

Cada arquivo roda no `resty`. Os testes usam `crescent.utils.tests` e podem chamar a aplicação sem servidor, com `app:handle`:

```lua
package.path = "./?.lua;./?/init.lua;" .. package.path

local tests = require("crescent.utils.tests")
local Crescent = require("crescent")
local json = require("crescent.json")

local function greets_by_name()
    local app = Crescent.new({ environment = "test", debug = true, root = ".", logger = function() end })
    require("src.hello").register(app)

    local writer = { headers = {} }
    app:handle({ method = "GET", path = "/api/hello", headers = {}, query = { name = "Ada" } }, writer)

    tests.assertEquals(writer.status, 200)
    tests.assertEquals(json.decode(writer.body).message, "Hello, Ada!")
end

assert(tests.runSuite("Hello", { greets_by_name = greets_by_name }))
```

Asserções disponíveis: `assertEquals`, `assertNotEquals`, `assertTrue`, `assertFalse`, `assertNil`, `assertNotNil`, `assertType`, `assertContains`, `assertNotContains`, `assertMatches`, `assertTableEquals`, `assertError`, `assertNoError`.

`test:http` roda a suíte de integração HTTP do repositório do framework (`tests/test-http.sh`); projetos novos não trazem esse arquivo.
