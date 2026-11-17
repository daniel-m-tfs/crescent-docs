# Banco de dados

## Configuração

O Crescent 2.0 suporta **somente MySQL/MariaDB**, via `lua-resty-mysql` (não bloqueia o worker). A conexão vem de `config.database`:

```lua
-- config/development.lua
database = {
    host = Env.get("DB_HOST", "127.0.0.1"),
    port = Env.number("DB_PORT", 3306),
    database = Env.get("DB_NAME", "meu_app_dev"),
    user = Env.get("DB_USER", "crescent"),
    password = Env.get("DB_PASSWORD", ""),
},
```

`Crescent.new(config)` configura o banco no boot (sem abrir conexão: cada query pega uma conexão do pool do worker). A partir daí, models e query builder usam esse banco automaticamente, e as actions o recebem em `ctx.db`.

| Chave opcional | Padrão | Descrição |
| --- | --- | --- |
| `charset` | `"utf8mb4"` | charset da conexão |
| `connect_timeout` / `timeout` | `5000` / `10000` | em ms |
| `pool_size` | `100` | conexões mantidas por worker |
| `max_idle_timeout` | `10000` | tempo ocioso no pool (ms) |
| `ssl`, `ssl_verify` | — | TLS com o MySQL |

SQL direto, sempre com `?` (os valores são escapados):

```lua
local rows, err = ctx.db:query("SELECT id, name FROM users WHERE email = ?", { email })
local result = ctx.db:execute("UPDATE users SET name = ? WHERE id = ?", { "Ada", 1 })
-- result = { affected_rows = 1, insert_id = 0 }
```

Erros retornam `nil, err, errno, sqlstate, kind`, em que `kind` é `"unique_violation"`, `"foreign_key_violation"`, `"deadlock"`, `"lock_timeout"`, `"connection"`, `"bind"` ou `"query"`.

## Models

```lua
-- src/users/models/user.lua
local Model = require("crescent.model")

return Model:extend({
    table = "users",
    fillable = { "name", "email", "password" },  -- campos aceitos em create/update
    hidden = { "password" },                     -- fora de to_table()
    timestamps = true,                           -- created_at / updated_at
    validates = {
        name = { required = true, min_length = 3 },
        email = { required = true, email = true, unique = true },
    },
})
```

`bin/crescent make:model User users` gera um esqueleto em `src/users/models/user.lua`. As regras de `validates` são as mesmas de [Validação](#validação), mais `unique = true` (consulta o banco; mantenha também um índice `UNIQUE`).

### CRUD

```lua
local User = require("src.users.models.user")

local user, errors = User:create({ name = "Ada", email = "ada@example.com" })
if not user then
    return ctx:error(422, "validation failed", errors, "validation_failed")
end

local user = User:find(1)                    -- model ou nil
local user = User:find_or_fail(1)            -- lança 404 model_not_found
local admins = User:where("role", "admin"):order_by("name"):get()
local first = User:where("email", email):first()
local total = User:count()

user.name = "Ada Lovelace"
user:save()                                  -- UPDATE só das colunas alteradas
user:update({ name = "Ada Byron" })          -- fill + save
user:delete()

return ctx:json(200, { data = user:to_table() })
```

- `create`, `save` e `update` retornam o model, ou `nil, erros`. Erros de validação (e de chave única do MySQL) chegam como tabela `{ campo = { { code, message } } }`; falhas de banco chegam como string.
- `User:where(...)` aceita o mesmo encadeamento do [query builder](#query-builder) e termina em `get()`, `first()`, `count()` ou `page()`.
- `user.name` lê o atributo. Se a coluna tiver o nome de um método do model (`table`, `save`, `update`...), use `user:get("coluna")` e `user:set("coluna", valor)`.
- Converta para JSON com `user:to_table()`; ela respeita `hidden` e inclui relações carregadas.
- O último argumento opcional de todos os métodos é o adaptador de banco (por exemplo, a transação `tx`).

### Paginação

```lua
local result = User:where("active", 1):order_by("name"):page(ctx.query.page, ctx.query.per_page)
-- result.data = { models }
-- result.meta = { page, per_page, total, last_page, from, to }
```

Valores inválidos voltam ao padrão (página 1, 15 por página) e `per_page` é limitado a 100 (passe `{ max_per_page = n }` como terceiro argumento para mudar).

### Tipos das colunas (casts)

O MySQL devolve `BIGINT` como string. O model converte automaticamente a chave primária e colunas `*_id` para número. Para outras colunas, declare `casts`:

```lua
casts = { active = "boolean", price = "number", external_id = "string" },
```

Tipos: `string`, `number`, `integer`, `boolean` (`1`/`0` vira `true`/`false`).

### Soft deletes

```lua
return Model:extend({ table = "users", soft_deletes = true })   -- precisa da coluna deleted_at
```

- `user:delete()` grava `deleted_at`; consultas passam a ignorar o registro.
- `User:with_trashed()` inclui os apagados; `User:only_trashed()` traz só eles.
- `user:restore()` desfaz; `user:force_delete()` apaga de verdade.

### Hooks

Funções na definição do model que recebem a instância. Um hook `before_*` que retorna `false` cancela a operação.

```lua
before_save = function(user)
    user.email = user.email:lower()
end,
```

Disponíveis: `before_save`, `before_create`, `before_update`, `after_create`, `after_update`, `after_save`, `before_delete`, `after_delete`.

## Relações

Declare as relações na tabela `relations`. `model` pode ser o nome do módulo (resolvido sob demanda, evita `require` circular):

```lua
-- users
relations = {
    posts = { type = "has_many", model = "src.blog.models.post" },
    profile = { type = "has_one", model = "src.users.models.profile" },
},

-- posts
relations = {
    user = { type = "belongs_to", model = "src.users.models.user" },
},
```

| Tipo | Chave estrangeira padrão |
| --- | --- |
| `has_many`, `has_one` | singular da tabela do pai + `_id`, na tabela relacionada (`users` → `user_id`) |
| `belongs_to` | singular da tabela relacionada + `_id`, na própria tabela |

Informe `foreign_key` (e `local_key`/`owner_key`) quando o padrão não servir.

Eager loading com `with`: uma query por relação para todos os registros, sem N+1.

```lua
local users = User:with("posts"):get()
users[1].posts                    -- lista de Post

local posts = Post:with("user", "comments.author"):get()   -- relações aninhadas

-- restringir a query da relação
User:query():with({ posts = function(q) q:order_by("created_at", "DESC") end }):get()
```

Sem eager loading, `user:get("posts")` carrega a relação na primeira chamada (`user.posts` só funciona depois de carregada).

## Query builder

Para consultas sem model (os resultados são tabelas simples):

```lua
local QueryBuilder = require("crescent.database.query_builder")

local rows = QueryBuilder.table("users")
    :select("users.id", "users.name", "profiles.bio")
    :left_join("profiles", "profiles.user_id", "users.id")
    :where("active", true)
    :where("age", ">=", 18)
    :where(function(q) q:where("role", "admin"):or_where("verified", true) end)
    :where_in("country", { "BR", "PT" })
    :order_by("users.name")
    :limit(20)
    :get()
```

| Grupo | Métodos |
| --- | --- |
| Filtros | `where`, `or_where`, `where_in`, `where_not_in`, `where_null`, `where_not_null`, `where_raw(sql, bindings)` |
| Junções | `join`, `left_join`, `right_join` |
| Ordem e limite | `order_by(coluna, "ASC" ou "DESC")`, `limit`, `offset`, `paginate(página, por_página)` |
| Execução | `get()`, `first()`, `count()`, `exists()`, `page(página, por_página)` |
| Escrita | `insert(valores)`, `update(valores)`, `delete()` |
| Depuração | `to_sql()` retorna `sql, bindings` sem executar |

- Operadores aceitos: `=`, `!=`, `<>`, `<`, `<=`, `>`, `>=`, `LIKE`, `NOT LIKE`. `where("coluna", nil)` gera `IS NULL`.
- `update` e `delete` sem `where` lançam erro (proteção contra alterar a tabela inteira).
- Linhas do query builder não passam pelos casts: ids `BIGINT` chegam como string.
- `QueryBuilder.raw(sql, bindings)` executa SQL livre.

## Transações

```lua
local Database = require("crescent.database")

local user, err = Database.transaction(function(tx)
    local user = assert(User:create({ name = "Ada", email = "ada@example.com" }, tx))
    tx:execute("INSERT INTO audit (user_id) VALUES (?)", { user.id })
    return user
end)
```

- Faz `COMMIT` quando a função retorna normalmente e `ROLLBACK` quando ela lança erro, retorna `false` ou `nil, err`.
- Passe `tx` como último argumento para models e query builder (`User:create(attrs, tx)`, `QueryBuilder.table("users"):get(tx)`), senão eles usam outra conexão, fora da transação.
- `tx:transaction(fn)` aninhado usa `SAVEPOINT`.

## Migrations

```bash
bin/crescent make:migration create_orders_table   # migrations/AAAAMMDDHHMMSS_create_orders_table.lua
bin/crescent db:migrate                           # aplica as pendentes
bin/crescent db:status                            # lista o que rodou
bin/crescent db:rollback                          # desfaz o último lote (batch)
```

Cada migration retorna `up` e `down`, que devolvem uma string SQL ou uma lista delas:

```lua
return {
    up = function(db)
        return {
            [[CREATE TABLE `orders` (
                `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                `user_id` BIGINT UNSIGNED NOT NULL,
                `total` DECIMAL(10,2) NOT NULL,
                `created_at` TIMESTAMP NULL,
                `updated_at` TIMESTAMP NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4]],
            "CREATE INDEX `orders_user_id` ON `orders` (`user_id`)",
        }
    end,
    down = function(db)
        return "DROP TABLE `orders`"
    end,
}
```

- Os arquivos rodam em ordem de nome e ficam registrados na tabela `migrations`. Cada execução de `db:migrate` forma um lote.
- O arquivo gerado por `make:migration` vem com uma tabela `example` de exemplo: edite antes de rodar.
- **DDL do MySQL faz commit implícito**: migrations não rodam em transação. Se uma migration com vários comandos falhar no meio, ela fica parcialmente aplicada e sem registro. Prefira um comando de schema por migration.

## Seeders

```bash
bin/crescent make:seeder admin_user    # cria seeds/admin_user.lua
bin/crescent db:seed                   # roda todos, em ordem de nome
bin/crescent db:seed admin_user        # só um
```

```lua
-- seeds/admin_user.lua
local User = require("src.users.models.user")

return function(db)
    if not User:where("email", "admin@example.com"):first(db) then
        assert(User:create({ name = "Admin", email = "admin@example.com" }, db))
    end
end
```

Cada seeder roda em uma transação (erro ou `return false` desfaz). Não há registro de execução, então escreva seeders idempotentes, como acima.

Referência completa (adaptador, bindings, testes com banco falso): [docs/database.md do framework](https://github.com/daniel-m-tfs/crescent-framework/blob/main/docs/database.md).
