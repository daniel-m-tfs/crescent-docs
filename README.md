# 📚 Sistema de Documentação do Crescent Framework# 🌙 Crescent Framework - Documentation



Este diretório contém o sistema de documentação modular do Crescent Framework.Official documentation website for Crescent Framework.



## 📁 Estrutura**Live Site:** https://crescent.tyne.com.br



```## 📁 Structure

crescent-docs/

├── docs/                          # 📝 Arquivos Markdown fonte```

│   ├── getting-started.md         # 🚀 Instalação e primeiros passossite/

│   ├── core-concepts.md           # 🎯 Rotas, Controllers, Services, Models├── index.html       # Homepage

│   ├── database.md                # 🗄️ ORM, Migrations, Query Builder├── docs.html        # Documentation

│   ├── cli.md                     # 🛠️ Comandos do CLI├── styles.css       # Global styles

│   ├── utilities.md               # 🧰 Testes, Hash, Helpers├── docs.css         # Docs styles

│   └── deployment.md              # 🚀 Deploy, NGINX, SSL, Systemd├── sitemap.xml      # Sitemap

│└── robots.txt       # SEO

├── docs.html                      # 🌐 HTML gerado (PUBLICAR ESTE)```

├── docs-backup.html               # 💾 Backup do HTML anterior

├── convert-docs.py                # 🔧 Script de conversão MD → HTML## 🚀 Development

├── styles.css                     # 🎨 Estilos gerais

└── docs.css                       # 🎨 Estilos específicos da documentaçãoJust open `index.html` in a browser or use a local server:

```

```bash

## 🔄 Workflow de Atualização# Python

python3 -m http.server 8000

### 1. Editar Documentação

# Node.js

Edite os arquivos `.md` na pasta `docs/`:npx http-server



```bash# PHP

# Editar seção de ORMphp -S localhost:8000

nano docs/database.md```



# Adicionar novo comando CLI## 🎨 Features

nano docs/cli.md

```- Netflix-style hero with animations

- Fully responsive design

### 2. Regenerar HTML- Mobile hamburger menu

- Syntax highlighting with Prism.js

Execute o script de conversão:- SEO optimized

- Open Graph meta tags

```bash

python3 convert-docs.py## 📝 Content

```

To update documentation, edit `docs.html`.

O script irá:

- ✅ Ler todos os 6 arquivos Markdown## 🤝 Contributing

- ✅ Converter para HTML com syntax highlighting

- ✅ Gerar navegação automática com linksFound a typo or want to improve the docs? PRs welcome!

- ✅ Adicionar estilos para code blocks e boxes

- ✅ Criar `docs.html` completo## 🔗 Links



### 3. Verificar Resultado- **Framework:** https://github.com/daniel-m-tfs/crescent-framework

- **Starter:** https://github.com/daniel-m-tfs/crescent-starter

Abra `docs.html` no navegador para verificar:- **LuaRocks:** https://luarocks.org/modules/crescent


```bash
open docs.html  # macOS
xdg-open docs.html  # Linux
```

### 4. Publicar

Faça commit e push:

```bash
git add docs/ docs.html convert-docs.py
git commit -m "docs: atualizar documentação do ORM"
git push origin main
```

## 📊 Estatísticas Atuais

**Conteúdo processado:**
- 📁 6 arquivos Markdown modulares
- 📄 68 seções individuais
- 📏 ~4177 linhas de HTML gerado
- 🔗 68 links de navegação automáticos

## 🎨 Elementos de Markdown Suportados

### Code Blocks
````markdown
```lua
local Router = require('crescent.core.router')
```
````

### Listas
```markdown
- Item não ordenado
1. Item ordenado
```

### Links
```markdown
[Texto](https://url.com)
[Seção](#secao-id)
```

### Formatação
```markdown
**Negrito**
*Itálico*
`código inline`
```

## 🔧 Como Funciona

O script `convert-docs.py` faz:

1. **Lê** todos os arquivos `.md` da pasta `docs/`
2. **Converte** Markdown para HTML válido
3. **Extrai** seções (H2) para criar âncoras de navegação
4. **Gera** menu lateral automático com links
5. **Injeta** CSS inline para boxes e estilos
6. **Cria** arquivo `docs.html` completo e auto-contido

## 📝 Licença

MIT License - Crescent Framework 2026
