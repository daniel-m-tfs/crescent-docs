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
├── convert-docs.py           # 🔧 Gera docs.html a partir de docs/*.md
├── docs-template.html        # 🧩 "Chrome" estático (head/SEO/navbar/footer/scripts)
├── index.html                # Homepage
├── docs.html                 # 🌐 GERADO — não edite direto, rode convert-docs.py
├── styles.css                # Estilos globais (site institucional)
├── docs.css                  # Estilos específicos da documentação
├── menu.css / menu.js        # Menu de navegação do topo
├── script.js / docs.js       # Comportamento do site (scroll, copy button, etc)
├── sitemap.xml / robots.txt  # SEO
```

## 🔧 `docs.html` é gerado — nunca edite direto

`docs/*.md` é a única fonte de verdade. `docs.html` é gerado por
`convert-docs.py` (Python 3, só biblioteca padrão, sem instalar nada) a
partir do `docs-template.html` (que tem o `<head>`/SEO/navbar/footer/scripts
estáticos, preservados intactos) + o conteúdo renderizado de cada `.md`.

Editar documentação:

1. Edite o `.md` correspondente em `docs/`.
2. Rode `python3 convert-docs.py` na raiz do repo — regenera `docs.html`
   inteiro (sidebar de navegação + todas as seções).
3. Confira o resultado abrindo `docs.html` num navegador antes de publicar.

O gerador cobre: headers (`#`-`####`), blocos de código com syntax
highlighting (Prism.js), tabelas GFM, listas ordenadas/não-ordenadas,
negrito/itálico/código inline, links (inclusive `/docs/arquivo` → âncora
interna da seção certa, já que tudo vira uma página única), `---` como
separador de seção, e blockquotes (`>`) como caixas `.note-box`. IDs de
seção são desambiguados automaticamente quando o mesmo título (ex. "Boas
Práticas") aparece em mais de um `.md`.

Nunca edite `docs.html` manualmente — a próxima execução de
`convert-docs.py` sobrescreve qualquer mudança feita direto nele.

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
edite só os arquivos em `docs/` e rode `python3 convert-docs.py` antes de
commitar (ver seção acima). Não edite `docs.html` direto.

## 🔗 Links

- **Framework:** https://github.com/daniel-m-tfs/crescent-framework
- **Starter:** https://github.com/daniel-m-tfs/crescent-starter
- **LuaRocks:** https://luarocks.org/modules/crescent

## 📝 Licença

MIT License - Crescent Framework 2026
