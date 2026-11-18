# Deploy

## Imagem Docker

O `Dockerfile` do projeto gera a imagem de produção:

```bash
docker build -t meu-app .

docker run -d -p 8080:8080 \
  -e APP_ENV=production \
  -e DB_HOST=db.interno -e DB_NAME=meu_app -e DB_USER=meu_app -e DB_PASSWORD=... \
  -e APP_KEY=... -e JWT_SECRET=... \
  -e RUN_MIGRATIONS=true \
  meu-app
```

O que a imagem faz:

- Parte de `openresty/openresty:*-alpine-fat` e instala as dependências Lua em uma camada própria.
- Roda como o usuário sem privilégios `crescent`; só `logs/`, `tmp/` e `storage/` são graváveis. Uploads vão para `storage/` (`upload_root = "storage"`): monte um volume nesse caminho para que sobrevivam a novos containers (o `docker-compose.yml` de desenvolvimento já usa o volume `app-storage`).
- Usa `conf/nginx.docker.conf`: cache de código ligado, `worker_processes auto`, app construído no `init_by_lua` e logs em stdout/stderr.
- Tem `HEALTHCHECK` em `/health`.
- Com `RUN_MIGRATIONS=true`, o entrypoint roda `bin/crescent db:migrate` antes de subir (até 10 tentativas, a cada 3 s, enquanto o banco não responde). O padrão da imagem é `false`.

Para rodar um comando avulso com a mesma imagem, passe-o como argumento:

```bash
docker run --rm --env-file prod.env meu-app bin/crescent db:migrate
```

Com várias réplicas, prefira rodar as migrations uma vez, num passo do deploy, em vez de `RUN_MIGRATIONS=true` em todas.

## Docker Compose (desenvolvimento)

O `docker-compose.yml` é para desenvolvimento:

```bash
cp .env.example .env
docker compose up --build
```

- Sobe a app e um MySQL 8.4 (exposto só em `127.0.0.1:3307`; dados no volume `mysql-data`).
- Usa `conf/nginx.docker-dev.conf`: um worker e `lua_code_cache off`, com o código montado em `/app` para recarga automática.
- Roda as migrations pendentes ao subir e cria o banco de testes (`DB_TEST_NAME`) na primeira inicialização do volume.
- `APP_PORT` muda a porta no host. As senhas do `.env.example` são só para desenvolvimento.
- Com `COMPOSE_PROFILES=redis` no `.env`, sobem também um Redis 7.4 (AOF ligado, senha `REDIS_PASSWORD`, exposto em `127.0.0.1:6380`, dados no volume `redis-data`) e o serviço `worker` (`bin/crescent queue:work`). Veja [Cache e filas](/docs/cache-queue).

Não use esse arquivo em produção: ele monta o código-fonte e desliga o cache de código.

## Sem Docker

Instale OpenResty, LuaRocks e as dependências (`./deps.sh`) no servidor e use `conf/nginx.production.conf` (revise antes):

```bash
APP_ENV=production openresty -p /srv/app/ -c conf/nginx.production.conf

# ou, de dentro do projeto
bin/crescent server start --conf conf/nginx.production.conf --env production
```

- `-p` é a raiz do projeto (com `/` no final): caminhos relativos, `.env`, `logs/` e o `lua_package_path` partem dela.
- O arquivo traz `user nobody;` (só tem efeito quando o master roda como root), `worker_processes auto`, `lua_code_cache on`, access log em JSON e timeouts de cliente.
- O `init_by_lua_block { require("app") }` constrói o app no master: um erro de configuração faz o start ou o `reload` falhar, em vez de quebrar a primeira requisição.
- Deploy de código novo: atualize os arquivos e rode `openresty -p /srv/app/ -c conf/nginx.production.conf -s reload` (ou `bin/crescent server reload --conf conf/nginx.production.conf`).
- O caminho do bundle de CAs (`lua_ssl_trusted_certificate`) é o do Debian/Ubuntu; ajuste em outras distribuições.

Use o supervisor do seu sistema (systemd, por exemplo) para iniciar o OpenResty no boot e repassar as variáveis de ambiente.

## Variáveis de ambiente

| Variável | Uso |
| --- | --- |
| `APP_ENV` | ambiente (`development`, `production`, `test`); escolhe `config/<APP_ENV>.lua` |
| `APP_DEBUG` | `true` mostra detalhes de erros (só desenvolvimento) |
| `APP_KEY` | segredo de cookies assinados, sessões e CSRF (32+ caracteres) |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | conexão MySQL |
| `DB_TEST_NAME` | banco usado pelo ambiente `test` |
| `JWT_SECRET` | segredo do `auth.jwt()` (32+ bytes) |
| `PASSWORD_HASH_ITERATIONS` | iterações do PBKDF2 (padrão 600000) |
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_FROM_NAME` | e-mail |
| `CACHE_DRIVER`, `QUEUE_DRIVER` | `shared` (memória do servidor, padrão) ou `redis`; a fila também aceita `sync` |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB` | conexão Redis (só usada pelos drivers `redis`) |
| `NGINX_CONF`, `RUN_MIGRATIONS` | Docker: configuração do Nginx e migrations ao subir |
| `APP_PORT`, `DB_FORWARD_PORT`, `DB_ROOT_PASSWORD`, `COMPOSE_PROFILES`, `REDIS_FORWARD_PORT` | Docker Compose |

Gere segredos com `openssl rand -base64 48`.

> Cada variável lida pela aplicação precisa de uma diretiva `env NOME;` em **todos** os arquivos do Nginx que você usa (`nginx.conf` e `conf/*.conf`). Ao criar uma variável nova, acrescente a diretiva, senão ela chega vazia nos workers.

## TLS, proxy e IP real

Normalmente o TLS termina num balanceador ou proxy na frente do OpenResty. Nesse caso, faça o Nginx confiar no IP informado pelo proxy, descomentando no `conf/nginx.production.conf` (ou `nginx.docker.conf`):

```nginx
set_real_ip_from 10.0.0.0/8;          # rede do seu balanceador
real_ip_header X-Forwarded-For;
real_ip_recursive on;
```

Assim `ctx.remote_addr` (usado pelo rate limit e pelos logs) passa a ser o IP do cliente. Nunca confie no `X-Forwarded-For` sem isso: qualquer cliente pode forjá-lo.

Para terminar o TLS no próprio OpenResty, ajuste o bloco `server`:

```nginx
server {
    listen 443 ssl;
    server_name app.example.com;
    ssl_certificate     /etc/letsencrypt/live/app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;

    location /public/ {
        alias public/;
        expires 1h;
    }

    location / {
        content_by_lua_block {
            require("app"):run()
        }
    }
}
```

Com o site 100% em HTTPS, ligue `hsts = true` no middleware de [headers de segurança](#headers-de-segurança). Arquivos estáticos ficam em `public/` e são servidos pelo Nginx em `/public/`, sem passar pelo Lua.

## Workers de fila

Com `QUEUE_DRIVER=shared`, os jobs rodam dentro do próprio OpenResty: o `init_worker_by_lua` dos confs chama `app:start_workers()`. Não há processo extra, mas os jobs pendentes se perdem num restart e cada servidor só processa a própria fila.

Com várias réplicas ou jobs que não podem se perder, use `QUEUE_DRIVER=redis` em todos os containers e rode workers com a mesma imagem:

```bash
docker run -d --env-file prod.env meu-app bin/crescent queue:work
docker run -d --env-file prod.env meu-app bin/crescent queue:work --queue=mail
```

- Escale rodando mais containers de worker; cada um processa um job por vez.
- Um job cujo worker morre (deploy, OOM) volta para a fila quando passa o `timeout` dele: escreva handlers idempotentes.
- O `HEALTHCHECK` da imagem testa o HTTP; desligue-o nos containers de worker (`healthcheck: disable: true` no compose).
- `--max-time=3600` faz o worker sair depois de uma hora para o orquestrador reiniciá-lo, o que ajuda com vazamentos de memória em jobs.
- Os logs dos jobs saem em JSON no stdout do worker.

## Logs e observabilidade

- **Access log** do Nginx: uma linha JSON por requisição com horário, request id (`rid`), IP, método, URI, status, bytes e duração. É a fonte de verdade do tráfego.
- **Error log**: erros do Nginx e as entradas JSON do `crescent.logger` (log por requisição, erros 500 com request id).
- No Docker, os dois vão para stdout/stderr (`docker logs`); fora dele, para `logs/`.
- `X-Request-Id`: o Crescent mantém o do proxy quando ele envia um, senão usa o `$request_id` do Nginx, e devolve o valor na resposta. Use-o para cruzar logs.
- `/health` (liveness) e `/ready` (readiness, verifica o banco e, quando usado, o Redis). Veja [Health e readiness](#health-e-readiness).

## Checklist de produção

- `APP_ENV=production` e `debug = false` (o `config/production.lua` já define).
- `APP_KEY` e `JWT_SECRET` com 32+ caracteres, fora do repositório; nada de `.env` em produção.
- Usuário do MySQL com acesso só ao banco da aplicação; migrations aplicadas no deploy.
- Toda variável nova declarada com `env NOME;` nos arquivos do Nginx.
- `client_max_body_size` e limites de upload ajustados ao que a aplicação aceita.
- `set_real_ip_from` configurado se houver proxy; rate limit no login.
- HSTS só com HTTPS em todo o site; CORS com lista explícita de origens.
- Balanceador usando `/ready`; orquestrador reiniciando por `/health`.
- `lua_shared_dict` (`crescent_limits`, `crescent_jwt`, `crescent_sessions`, `crescent_cache`, `crescent_queue`) mantidos no conf; lembre que eles são locais a cada servidor.
- Mais de uma réplica: `CACHE_DRIVER=redis` e `QUEUE_DRIVER=redis`, Redis com senha e fora da internet pública, e workers rodando `queue:work`.
