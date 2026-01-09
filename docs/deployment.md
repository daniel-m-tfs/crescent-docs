# 🚀 Deployment & Production

Guia completo para colocar sua aplicação Crescent em produção.

---

## 📋 Pré-requisitos

### Servidor Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y curl git build-essential libssl-dev

# CentOS/RHEL
sudo yum install -y curl git gcc make openssl-devel
```

### Instalar Luvit

```bash
curl -L https://github.com/luvit/lit/raw/master/get-lit.sh | sh
```

Adicionar ao PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Instalar NGINX

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS/RHEL
sudo yum install -y nginx

# Iniciar e habilitar
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Instalar MySQL/MariaDB

```bash
# Ubuntu/Debian
sudo apt install -y mysql-server

# CentOS/RHEL
sudo yum install -y mariadb-server

# Iniciar
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure installation
sudo mysql_secure_installation
```

---

## 🔧 Configuração do Projeto

### 1. Clonar Projeto

```bash
cd /var/www
sudo git clone https://github.com/seu-usuario/seu-projeto.git meu-app
sudo chown -R $USER:$USER /var/www/meu-app
cd /var/www/meu-app
```

### 2. Instalar Dependências

```bash
# Crescent Framework
lit install daniel-m-tfs/crescent-framework

# Outras dependências (se houver)
lit install luvit/secure-socket
lit install luvit/json
```

### 3. Configurar Ambiente

```bash
cp .env.example .env
nano .env
```

```bash
# .env (produção)
APP_ENV=production
APP_PORT=8080
APP_HOST=127.0.0.1

DB_HOST=localhost
DB_PORT=3306
DB_NAME=meu_banco_producao
DB_USER=meu_usuario
DB_PASSWORD=senha_forte_aqui

JWT_SECRET=chave_super_secreta_aleatoria_64_caracteres_ou_mais
```

### 4. Criar Banco de Dados

```bash
mysql -u root -p
```

```sql
CREATE DATABASE meu_banco_producao CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'meu_usuario'@'localhost' IDENTIFIED BY 'senha_forte_aqui';
GRANT ALL PRIVILEGES ON meu_banco_producao.* TO 'meu_usuario'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Executar Migrations

```bash
luvit crescent-cli migrate
```

---

## 🌐 NGINX Reverse Proxy

### Configuração Básica

```nginx
# /etc/nginx/sites-available/meu-app
server {
    listen 80;
    server_name meuapp.com www.meuapp.com;

    # Logs
    access_log /var/log/nginx/meu-app-access.log;
    error_log /var/log/nginx/meu-app-error.log;

    # Proxy para Luvit
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        
        # Headers importantes
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Cache bypass
        proxy_cache_bypass $http_upgrade;
    }

    # Arquivos estáticos (se houver)
    location /static {
        alias /var/www/meu-app/public;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Habilitar Site

```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/meu-app /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar NGINX
sudo systemctl reload nginx
```

---

## 🔒 SSL/HTTPS com Let's Encrypt

### Instalar Certbot

```bash
# Ubuntu/Debian
sudo apt install -y certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install -y certbot python3-certbot-nginx
```

### Obter Certificado

```bash
sudo certbot --nginx -d meuapp.com -d www.meuapp.com
```

### Configuração NGINX com SSL

```nginx
# /etc/nginx/sites-available/meu-app
server {
    listen 80;
    server_name meuapp.com www.meuapp.com;
    
    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name meuapp.com www.meuapp.com;

    # SSL
    ssl_certificate /etc/letsencrypt/live/meuapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/meuapp.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS (opcional mas recomendado)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logs
    access_log /var/log/nginx/meu-app-access.log;
    error_log /var/log/nginx/meu-app-error.log;

    # Proxy para Luvit
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        proxy_cache_bypass $http_upgrade;
    }

    # Arquivos estáticos
    location /static {
        alias /var/www/meu-app/public;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Renovação Automática

```bash
# Testar renovação
sudo certbot renew --dry-run

# Crontab para renovação automática
sudo crontab -e
```

Adicionar:
```
0 0 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## 🔧 Systemd Service

### Criar Service Unit

```bash
sudo nano /etc/systemd/system/meu-app.service
```

```ini
[Unit]
Description=Crescent Framework Application
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/meu-app
Environment="PATH=/home/www-data/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="APP_ENV=production"
ExecStart=/home/www-data/.local/bin/luvit bootstrap.lua
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=meu-app

# Segurança
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/meu-app

[Install]
WantedBy=multi-user.target
```

### Gerenciar Service

```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar (iniciar no boot)
sudo systemctl enable meu-app

# Iniciar
sudo systemctl start meu-app

# Status
sudo systemctl status meu-app

# Parar
sudo systemctl stop meu-app

# Reiniciar
sudo systemctl restart meu-app

# Logs em tempo real
sudo journalctl -u meu-app -f
```

---

## 📊 Monitoramento e Logs

### Logs Systemd

```bash
# Últimas 100 linhas
sudo journalctl -u meu-app -n 100

# Seguir em tempo real
sudo journalctl -u meu-app -f

# Filtrar por data
sudo journalctl -u meu-app --since "2026-01-09"

# Filtrar por prioridade
sudo journalctl -u meu-app -p err
```

### Logs NGINX

```bash
# Access log
sudo tail -f /var/log/nginx/meu-app-access.log

# Error log
sudo tail -f /var/log/nginx/meu-app-error.log

# Analisar códigos de status
awk '{print $9}' /var/log/nginx/meu-app-access.log | sort | uniq -c | sort -rn

# Top 10 IPs
awk '{print $1}' /var/log/nginx/meu-app-access.log | sort | uniq -c | sort -rn | head -10
```

### Logs da Aplicação

```lua
-- Implementar logger
local Logger = {}

function Logger:log(level, message, data)
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    local logEntry = string.format(
        "[%s] [%s] %s",
        timestamp,
        level,
        message
    )
    
    if data then
        logEntry = logEntry .. " " .. require('json').encode(data)
    end
    
    print(logEntry)  -- systemd captura isso
end

function Logger:info(message, data)
    self:log("INFO", message, data)
end

function Logger:error(message, data)
    self:log("ERROR", message, data)
end

return Logger
```

---

## ⚡ Performance

### NGINX Optimizations

```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Básico
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Buffer
    client_body_buffer_size 128k;
    client_max_body_size 10M;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;
    gzip_disable "msie6";
    
    # Cache estático
    open_file_cache max=10000 inactive=30s;
    open_file_cache_valid 60s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=3r/s;
}
```

### MySQL Optimization

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

```ini
[mysqld]
# InnoDB
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# Query cache
query_cache_size = 64M
query_cache_type = 1

# Connections
max_connections = 200

# Logs (desabilitar em produção para performance)
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
```

Aplicar:
```bash
sudo systemctl restart mysql
```

---

## 🔐 Segurança

### Firewall (UFW)

```bash
# Habilitar UFW
sudo ufw enable

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verificar status
sudo ufw status
```

### Fail2Ban

```bash
# Instalar
sudo apt install -y fail2ban

# Configurar
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
```

```bash
# Iniciar
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Status
sudo fail2ban-client status
```

### Hardening MySQL

```sql
-- Remover usuários anônimos
DELETE FROM mysql.user WHERE User='';

-- Remover banco de teste
DROP DATABASE IF EXISTS test;

-- Permitir root apenas localmente
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

FLUSH PRIVILEGES;
```

### Variáveis de Ambiente Seguras

```bash
# Nunca commite .env no Git!
# Usar variáveis do sistema

sudo nano /etc/systemd/system/meu-app.service
```

```ini
[Service]
Environment="DB_PASSWORD=senha_segura_aqui"
Environment="JWT_SECRET=token_secreto_aqui"
```

---

## 🔄 Deploy Automatizado

### Script de Deploy

```bash
#!/bin/bash
# deploy.sh

set -e  # Exit on error

APP_DIR="/var/www/meu-app"
BACKUP_DIR="/var/backups/meu-app"

echo "🚀 Starting deployment..."

# 1. Backup atual
echo "📦 Creating backup..."
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).tar.gz $APP_DIR

# 2. Pull código
echo "📥 Pulling latest code..."
cd $APP_DIR
git pull origin main

# 3. Instalar dependências
echo "📚 Installing dependencies..."
lit install

# 4. Migrations
echo "🗄️ Running migrations..."
luvit crescent-cli migrate

# 5. Reiniciar serviço
echo "🔄 Restarting service..."
sudo systemctl restart meu-app

# 6. Verificar status
echo "✅ Checking status..."
sleep 2
sudo systemctl status meu-app --no-pager

# 7. Reload NGINX
echo "🌐 Reloading NGINX..."
sudo nginx -t && sudo systemctl reload nginx

echo "✨ Deployment complete!"
```

Tornar executável:
```bash
chmod +x deploy.sh
```

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy via SSH
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_IP }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /var/www/meu-app
          ./deploy.sh
```

---

## 🩺 Health Checks

### Endpoint de Status

```lua
-- src/health/routes/health.lua
return function(router)
    router:get("/health", function(ctx)
        -- Verificar banco
        local db = require('crescent.database.mysql')
        local dbOk = pcall(function()
            db:query("SELECT 1")
        end)
        
        return ctx.json(200, {
            status = "ok",
            timestamp = os.date("%Y-%m-%d %H:%M:%S"),
            uptime = os.clock(),
            database = dbOk and "connected" or "disconnected"
        })
    end)
end
```

### Monitoramento Externo

```bash
# Criar script de verificação
nano /usr/local/bin/check-app.sh
```

```bash
#!/bin/bash

URL="https://meuapp.com/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $RESPONSE -eq 200 ]; then
    echo "✅ App is healthy"
    exit 0
else
    echo "❌ App is down (HTTP $RESPONSE)"
    # Reiniciar serviço
    sudo systemctl restart meu-app
    exit 1
fi
```

```bash
chmod +x /usr/local/bin/check-app.sh

# Cron a cada 5 minutos
crontab -e
```

```
*/5 * * * * /usr/local/bin/check-app.sh >> /var/log/app-health.log 2>&1
```

---

## 🐛 Troubleshooting

### App não inicia

```bash
# Verificar logs
sudo journalctl -u meu-app -n 100

# Verificar sintaxe Lua
luvit -e "require('bootstrap')"

# Verificar permissões
ls -la /var/www/meu-app
sudo chown -R www-data:www-data /var/www/meu-app
```

### Erro 502 Bad Gateway

```bash
# App está rodando?
sudo systemctl status meu-app

# Porta correta?
netstat -tulpn | grep 8080

# Testar localmente
curl http://localhost:8080
```

### Banco de dados não conecta

```bash
# MySQL está rodando?
sudo systemctl status mysql

# Testar conexão
mysql -h localhost -u meu_usuario -p meu_banco_producao

# Verificar .env
cat .env | grep DB_
```

### Logs grandes

```bash
# Limitar tamanho do journal
sudo journalctl --vacuum-time=7d
sudo journalctl --vacuum-size=500M

# Rotação de logs NGINX
sudo nano /etc/logrotate.d/nginx
```

```
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null
    endscript
}
```

---

## 📖 Próximas Seções

- **[Getting Started](/docs/getting-started)** - Instalação e início
- **[Core Concepts](/docs/core-concepts)** - Routes, Controllers, Services
- **[Database](/docs/database)** - ORM e Migrations
- **[CLI](/docs/cli)** - Comandos disponíveis
