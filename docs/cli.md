# CLI

## Usando a CLI

A CLI vem dentro do projeto. Rode-a da raiz do projeto com `lua cli.lua`:

```bash
lua cli.lua <comando> [argumentos]
lua cli.lua help
```

Geradores, `new`, `server` e `test` rodam no Lua comum (5.1 a 5.4 ou LuaJIT). Comandos que precisam do OpenResty (`db:*` e `routes`) são repassados automaticamente para `bin/crescent`, que roda no mesmo LuaJIT do OpenResty que atende as requisições (via `resty`). `bin/crescent <comando>` aceita os mesmos comandos e é o que se usa no Docker: `docker compose exec app bin/crescent <comando>`.

A CLI lê o `.env` da raiz do projeto (variáveis do ambiente têm prioridade). A saída é colorida no terminal; `NO_COLOR=1` desliga as cores.

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
lua cli.lua server start --conf conf/nginx.production.conf --env production
```

Erros de inicialização vão para `logs/error.log`.

## Desenvolvimento com Docker

| Comando | Descrição |
| --- | --- |
| `setup` | Prepara o projeto, perguntando antes de cada passo: (1) **git** — recomeça o histórico do zero (`git init`, branch `main`, commit inicial) sem o remote do template e, opcionalmente, adiciona o seu remote e faz o push; (2) **banco** — usuário e senha do MySQL do Docker gravados no `.env` (senha vazia = gerada; `DB_ROOT_PASSWORD` aleatória); (3) **Docker** — sobe a aplicação com `run`. |
| `run [--logs]` | `docker compose up -d`, espera o `/health` responder e mostra as URLs. O código fica montado no container com `lua_code_cache off`: alterações em `src/`, `views/` e `app.lua` valem na próxima requisição. `--logs` acompanha os logs da aplicação. |
| `rerun [--logs] [--fresh]` | Reconstrói a imagem e reinicia (`up -d --build`, com cache): use depois de mudar `Dockerfile`, dependências (`deps.sh`) ou configuração do Nginx. `--fresh` reconstrói sem cache. |
| `stop` | `docker compose down`: para os containers e mantém os volumes (banco e uploads). |

Se o volume do MySQL já existe, o `setup` avisa: o MySQL só lê usuário e senha ao criar o volume (`docker compose down -v` recria, apagando os dados do banco do Docker). O `setup` se recusa a rodar no repositório do próprio framework.

## Geradores

Os geradores **nunca sobrescrevem** arquivos e mostram cada arquivo criado (`✓ Controller  src/...`). `BlogPost` e `blog-post` viram `blog_post` em nomes de arquivo e `BlogPost` no código. Quando o módulo é omitido, ele recebe o próprio nome.

| Comando | Cria |
| --- | --- |
| `make:module <nome>` | módulo CRUD completo em `src/<nome>/`, teste e migration (veja abaixo) |
| `make:controller <nome> [módulo]` | `src/<módulo>/controllers/<nome>.lua` |
| `make:service <nome> [módulo]` | `src/<módulo>/services/<nome>.lua` |
| `make:model <nome> [módulo]` | `src/<módulo>/models/<nome>.lua` |
| `make:routes <nome> [módulo]` | `src/<módulo>/routes/<nome>.lua` |
| `make:middleware <nome> [módulo]` | `src/middleware/<nome>.lua` (ou dentro do módulo) |
| `make:test <nome>` | `tests/test-<nome>.lua` |
| `make:migration <nome>` | `migrations/AAAAMMDDHHMMSS_<nome>.lua` |
| `make:seeder <nome>` | `seeds/<nome>.lua` (prefixe com `01_` para definir a ordem) |
| `new <nome>` | novo projeto em `./<nome>` (a partir do repositório do framework) |

Nomes começam com letra e usam letras, números, `_` ou `-`. Migrations usam só letras, números e `_`; seeders também podem começar com número (`01_admin_user`). `make:action` (nome do 2.0.0) continua funcionando como alias de `make:controller`.

`make:migration` deduz a tabela do nome: `create_products_table` (ou `create_products`) gera um `CREATE TABLE products`; `add_price_to_products`, `remove_x_from_products` e `alter_products_table` geram um esqueleto de `ALTER TABLE products`.

### make:module

Todo módulo segue a mesma estrutura (a do Crescent 1.x):

```
src/<módulo>/
  init.lua          Module.register(app)
  controllers/      recebem ctx, chamam services e respondem (ctx:json, ctx:view, ctx:error)
  services/         regras de negócio, sem ctx (fáceis de testar)
  models/           Model:extend({ table, fillable, validates, ... })
  routes/           function(app, prefix) com rotas nomeadas
```

```bash
lua cli.lua make:module Product
```

```
🌙 Creating module Product

✓ Module      src/product/init.lua
✓ Controller  src/product/controllers/product.lua
✓ Service     src/product/services/product.lua
✓ Model       src/product/models/product.lua
✓ Routes      src/product/routes/product.lua
✓ Test        tests/test-product-module.lua
✓ Migration   migrations/20261117140952_create_products_table.lua

ℹ Register the module in app.lua:
    require("src.product").register(app)
ℹ Then create the table and run the module test:
    lua cli.lua db:migrate
    lua cli.lua test product
```

O controller traz `index`, `show`, `store`, `update`, `destroy` e o schema de validação; o service traz `page`, `find`, `create`, `update` e `delete`. Para acrescentar peças a um módulo existente, passe o módulo: `lua cli.lua make:controller Report product`. As rotas geradas estão em [Primeiro módulo](#primeiro-módulo).

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
lua cli.lua test             # todos os arquivos tests/test*.lua
lua cli.lua test product     # só os que contêm "product" no nome
lua cli.lua test:http        # tests/test-http.sh contra um OpenResty real
./test.sh                    # test + test:http
```

Cada arquivo roda no `resty`. A saída mostra cada teste (`✓`/`✗` com a mensagem de erro) e, no fim, um resumo com arquivos, testes, tempo e a lista dos arquivos que falharam:

```
🌙 Test summary

  Files:  3 run, 3 passed, 0 failed
  Tests:  5 run, 5 passed, 0 failed
  Time:   0s

✅ All tests passed! (3/3 files)
``` Os testes usam `crescent.utils.tests` e podem chamar a aplicação sem servidor, com `app:handle`:

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

`test:http` roda `tests/test-http.sh`: projetos novos trazem um teste que sobe o OpenResty com `APP_ENV=test` na porta 8080, confere `/health`, `/` e `/api/hello` com `curl` e para o servidor. Acrescente suas rotas com a função `expect <status> <caminho> [texto]`.
