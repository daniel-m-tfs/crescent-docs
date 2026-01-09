#!/usr/bin/env python3
"""
Script para converter os arquivos Markdown da documentação para HTML
e gerar o docs.html completo com navegação integrada.
"""

import re
import os
from pathlib import Path

def md_to_html(md_content):
    """Converte Markdown para HTML"""
    
    # STEP 1: Proteger code blocks e converter primeiro
    code_blocks = []
    def save_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2).strip()
        # Escape HTML
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        placeholder = f'___CODE_BLOCK_{len(code_blocks)}___'
        code_blocks.append(f'<div class="code-block"><pre><code class="language-{lang}">{code}</code></pre></div>')
        return placeholder
    
    html = re.sub(r'```(\w+)?\n(.*?)```', save_code_block, md_content, flags=re.DOTALL)
    
    # STEP 2: Headers
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # STEP 3: Horizontal rules
    html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)
    
    # STEP 4: Links (antes de bold/italic)
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # STEP 5: Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # STEP 6: Italic
    html = re.sub(r'(?<!\*)\*(?!\*)([^\*]+?)\*(?!\*)', r'<em>\1</em>', html)
    
    # STEP 7: Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # STEP 8: Lists
    lines = html.split('\n')
    result = []
    in_ul = False
    in_ol = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip placeholders
        if '___CODE_BLOCK_' in stripped:
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(line)
            continue
        
        # Unordered list
        ul_match = re.match(r'^- (.+)$', stripped)
        if ul_match:
            if not in_ul:
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append('<ul>')
                in_ul = True
            result.append(f'<li>{ul_match.group(1)}</li>')
            continue
        
        # Ordered list
        ol_match = re.match(r'^\d+\. (.+)$', stripped)
        if ol_match:
            if not in_ol:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                result.append('<ol>')
                in_ol = True
            result.append(f'<li>{ol_match.group(1)}</li>')
            continue
        
        # Not a list item
        if in_ul:
            result.append('</ul>')
            in_ul = False
        if in_ol:
            result.append('</ol>')
            in_ol = False
        
        result.append(line)
    
    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')
    
    html = '\n'.join(result)
    
    # STEP 9: Paragraphs (only wrap text that isn't already in tags)
    lines = html.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines, HTML tags, placeholders, horizontal rules
        if (not stripped or 
            stripped.startswith('<') or 
            '___CODE_BLOCK_' in stripped or
            stripped.startswith('|')):
            result.append(line)
        else:
            # Wrap in paragraph
            result.append(f'<p>{line}</p>')
    
    html = '\n'.join(result)
    
    # STEP 10: Restore code blocks
    for i, code_block in enumerate(code_blocks):
        html = html.replace(f'___CODE_BLOCK_{i}___', code_block)
    
    return html

def create_section_id(title):
    """Cria ID da seção a partir do título"""
    # Remove emojis e caracteres especiais
    section_id = re.sub(r'[^\w\s-]', '', title.lower())
    section_id = re.sub(r'[-\s]+', '-', section_id)
    return section_id.strip('-')

def extract_sections(md_content, file_name):
    """Extrai seções do Markdown"""
    sections = []
    current_section = None
    current_content = []
    
    lines = md_content.split('\n')
    skip_first_h1 = True
    
    for line in lines:
        # H2 headers iniciam novas seções
        if line.startswith('## '):
            if current_section:
                sections.append({
                    'id': create_section_id(current_section),
                    'title': current_section,
                    'content': '\n'.join(current_content),
                    'file': file_name
                })
            current_section = line[3:].strip()
            current_content = []
        elif line.startswith('# ') and skip_first_h1:
            # H1 é o título do arquivo - ignorar apenas o primeiro
            skip_first_h1 = False
            continue
        else:
            current_content.append(line)
    
    # Adiciona última seção
    if current_section:
        sections.append({
            'id': create_section_id(current_section),
            'title': current_section,
            'content': '\n'.join(current_content),
            'file': file_name
        })
    
    return sections

def generate_docs_html():
    """Gera o docs.html completo"""
    
    docs_dir = Path('docs')
    files = {
        'getting-started.md': '🚀 Começando',
        'core-concepts.md': '🎯 Core Concepts',
        'database.md': '🗄️ Database & ORM',
        'cli.md': '🛠️ CLI Tools',
        'utilities.md': '🧰 Utilities',
        'deployment.md': '🚀 Deployment'
    }
    
    all_sections = []
    nav_items = {}
    
    # Processar cada arquivo
    for filename, category in files.items():
        filepath = docs_dir / filename
        if not filepath.exists():
            print(f"⚠️  Arquivo não encontrado: {filepath}")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = extract_sections(content, filename)
        
        if category not in nav_items:
            nav_items[category] = []
        
        for section in sections:
            nav_items[category].append({
                'id': section['id'],
                'title': section['title']
            })
        
        all_sections.extend(sections)
    
    # Gerar HTML da navegação
    nav_html = ''
    for category, items in nav_items.items():
        nav_html += f'''                <div class="nav-section">
                    <h3>{category}</h3>
                    <ul>\n'''
        for item in items:
            nav_html += f'                        <li><a href="#{item["id"]}">{item["title"]}</a></li>\n'
        nav_html += '                    </ul>\n                </div>\n'
    
    # Gerar HTML das seções
    content_html = ''
    for section in all_sections:
        html_content = md_to_html(section['content'])
        content_html += f'''
            <section id="{section['id']}" class="doc-section">
                <h2>{section['title']}</h2>
                {html_content}
            </section>
'''
    
    # Template HTML completo
    full_html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="./crescent-logo-semfundo.ico">
    <link rel="shortcut icon" type="image/x-icon" href="./crescent-logo-semfundo.ico">
    <link rel="apple-touch-icon" href="./crescent-logo-semfundo.png">
    
    <!-- SEO Meta Tags -->
    <title>Documentação - Crescent Framework | Framework Web Lua Completo</title>
    <meta name="description" content="Documentação completa do Crescent Framework: aprenda a usar o framework web Lua com ORM, migrations, CLI e arquitetura modular. Tutoriais, exemplos e guias.">
    <meta name="keywords" content="documentação lua framework, crescent framework docs, lua web framework tutorial, guia lua web, lua orm documentation, crescent lua api, framework web lua guia">
    <meta name="author" content="Crescent Framework Team">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://crescent.tyne.com.br/docs.html">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://crescent.tyne.com.br/docs.html">
    <meta property="og:title" content="Documentação - Crescent Framework">
    <meta property="og:description" content="Documentação completa do framework web Lua: ORM, migrations, CLI e muito mais.">
    <meta property="og:image" content="https://crescent.tyne.com.br/crescent-logo-semfundo.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="Crescent Framework Logo">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://crescent.tyne.com.br/docs.html">
    <meta property="twitter:title" content="Documentação - Crescent Framework">
    <meta property="twitter:description" content="Documentação completa do framework web Lua: ORM, migrations, CLI e muito mais.">
    <meta property="twitter:image" content="https://crescent.tyne.com.br/crescent-logo-semfundo.png">
    <meta property="twitter:image:alt" content="Crescent Framework Logo">
    
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="docs.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <!-- Prism.js for syntax highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <style>
        /* Additional styles for documentation boxes */
        .info-box, .warning-box, .success-box, .danger-box, .note-box {{
            padding: 1rem 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0.5rem;
            border-left: 4px solid;
        }}
        
        .info-box {{
            background-color: #e7f3ff;
            border-color: #2196F3;
            color: #0d47a1;
        }}
        
        .warning-box {{
            background-color: #fff3cd;
            border-color: #ff9800;
            color: #8a6d3b;
        }}
        
        .success-box {{
            background-color: #d4edda;
            border-color: #28a745;
            color: #155724;
        }}
        
        .danger-box {{
            background-color: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }}
        
        .note-box {{
            background-color: #e8f5e9;
            border-color: #4caf50;
            color: #2e7d32;
        }}
        
        .doc-section {{
            scroll-margin-top: 2rem;
        }}
        
        .doc-section h2 {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 2px solid #eee;
        }}
        
        .doc-section h2:first-child {{
            margin-top: 0;
            border-top: none;
        }}
        
        .code-block {{
            margin: 1.5rem 0;
        }}
        
        .docs-nav a.active {{
            color: #667eea;
            font-weight: 600;
            background: rgba(102, 126, 234, 0.1);
        }}
        
        hr {{
            margin: 2rem 0;
            border: none;
            border-top: 2px solid #eee;
        }}
    </style>
</head>
<body class="docs-page">
    <!-- Navigation -->
    <nav class="navbar">
        <div class="container">
            <div class="nav-content">
                <div class="nav-brand">
                    <img src="./crescent-logo-semfundo.png" alt="Crescent Framework" class="logo">
                    <span class="brand-name">Crescent</span>
                </div>
                <button class="mobile-menu-toggle" aria-label="Toggle menu">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
                <ul class="nav-links">
                    <li><a href="index.html">Home</a></li>
                    <li><a href="index.html#features">Features</a></li>
                    <li><a href="index.html#getting-started">Get Started</a></li>
                    <li><a href="docs.html" class="active">Documentação</a></li>
                    <li><a href="https://github.com/daniel-m-tfs/crescent-framework" target="_blank" class="github-link">GitHub</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="docs-container">
        <!-- Sidebar -->
        <aside class="docs-sidebar">
            <nav class="docs-nav">
{nav_html}
            </nav>
        </aside>

        <!-- Main Content -->
        <main class="docs-content">
            <div class="hero-section">
                <h1>🌙 Crescent Framework</h1>
                <p class="lead">Framework web moderno e performático construído em Lua, Luvit e MySQL.</p>
                
                <div class="highlight-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-bottom: 2rem; padding: 2rem; border-radius: 1rem;">
                    <h3 style="color: white; margin-bottom: 0.75rem;">🚀 Comece Agora!</h3>
                    <p style="margin: 0.5rem 0; color: rgba(255, 255, 255, 0.95);">Baixe o Crescent Starter e comece a desenvolver em minutos:</p>
                    <a href="https://github.com/daniel-m-tfs/crescent-framework/releases/download/Versões/crescent-starter.zip" 
                       style="display: inline-block; background: white; color: #667eea; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none; font-weight: 700; margin-top: 0.75rem; transition: all 0.3s;"
                       onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 10px 20px rgba(0,0,0,0.2)'"
                       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        📦 Download crescent-starter.zip
                    </a>
                </div>
            </div>
{content_html}
        </main>
    </div>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>Crescent Framework</h3>
                    <p>Framework web Lua moderno e performático</p>
                </div>
                <div class="footer-section">
                    <h3>Links</h3>
                    <ul>
                        <li><a href="index.html">Home</a></li>
                        <li><a href="docs.html">Documentação</a></li>
                        <li><a href="https://github.com/daniel-m-tfs/crescent-framework">GitHub</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h3>Comunidade</h3>
                    <ul>
                        <li><a href="https://github.com/daniel-m-tfs/crescent-framework/issues">Issues</a></li>
                        <li><a href="https://github.com/daniel-m-tfs/crescent-framework/discussions">Discussões</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2026 Crescent Framework. MIT License.</p>
            </div>
        </div>
    </footer>

    <!-- Scripts -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <script src="script.js"></script>
    <script>
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});

        // Active link highlighting
        const sections = document.querySelectorAll('.doc-section');
        const navLinks = document.querySelectorAll('.docs-nav a');

        window.addEventListener('scroll', () => {{
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                const sectionHeight = section.clientHeight;
                if (pageYOffset >= sectionTop - 100) {{
                    current = section.getAttribute('id');
                }}
            }});

            navLinks.forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {{
                    link.classList.add('active');
                }}
            }});
        }});
    </script>
</body>
</html>'''
    
    # Salvar arquivo
    with open('docs.html', 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print("✅ docs.html gerado com sucesso!")
    print(f"📄 {len(all_sections)} seções processadas")

if __name__ == '__main__':
    generate_docs_html()
