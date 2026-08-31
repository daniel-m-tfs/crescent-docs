# 📚 Sistema de Documentação do Crescent Framework

Este repositório contém o site de documentação e o site institucional do Crescent Framework.

**Site publicado:** https://crescent.tyne.com.br

## 📁 Estrutura

```
crescent-docs/
├── docs/                    # 📝 Arquivos Markdown fonte (edite estes)
│   ├── getting-started.md   # 🚀 Instalação e primeiros passos
│   ├── core-concepts.md     # 🎯 Rotas, Controllers, Services, Models
│   ├── database.md          # 🗄️ ORM, Migrations, Query Builder
│   ├── cli.md                # 🛠️ Comandos do CLI
│   ├── utilities.md         # 🧰 Testes, Hash, Helpers
│   └── deployment.md        # 🚀 Deploy, NGINX, SSL, Systemd
├── index.html                # Homepage
├── docs.html                 # 🌐 Página de documentação publicada
├── styles.css                # Estilos globais (site institucional)
├── docs.css                  # Estilos específicos da documentação
├── menu.css / menu.js        # Menu de navegação do topo
├── script.js / docs.js       # Comportamento do site (scroll, copy button, etc)
├── sitemap.xml / robots.txt  # SEO
```

## ⚠️ Estado atual: `docs.html` é editado à mão

Hoje `docs/*.md` e `docs.html` são mantidos **manualmente em paralelo** — não
existe nenhum script conectando os dois. Um script de conversão
(`convert-docs.py`) chegou a existir, mas foi removido do repositório; esta
seção do README será atualizada assim que o gerador for reconstruído.

Isso já causou divergência real entre os dois: várias seções de `docs.html`
ficaram desatualizadas em relação ao `docs/*.md` correspondente. Ao editar
documentação:

1. Edite o `.md` correspondente em `docs/`.
2. Replique a mudança manualmente em `docs.html` (mesmo `id` de seção, mesmo
   conteúdo, HTML com entidades escapadas em vez de Markdown).
3. Confira visualmente abrindo `docs.html` num navegador antes de publicar.

## 🚀 Rodando localmente

```bash
# Python
python3 -m http.server 8000

# Node.js
npx http-server

# PHP
php -S localhost:8000
```

Depois abra `http://localhost:8000/index.html` ou `http://localhost:8000/docs.html`.

## 🎨 Features do site

- Hero animado, design responsivo, menu hambúrguer mobile
- Syntax highlighting com Prism.js
- Meta tags de SEO / Open Graph / Twitter Card
- Botão de copiar código, destaque de navegação por scroll (`docs.js`)

## 🤝 Contribuindo

Encontrou um erro ou quer melhorar a documentação? PRs são bem-vindos —
lembre de manter `docs/*.md` e `docs.html` em sincronia (ver seção acima)
até o gerador automatizado existir de novo.

## 🔗 Links

- **Framework:** https://github.com/daniel-m-tfs/crescent-framework
- **Starter:** https://github.com/daniel-m-tfs/crescent-starter
- **LuaRocks:** https://luarocks.org/modules/crescent

## 📝 Licença

MIT License - Crescent Framework 2026
