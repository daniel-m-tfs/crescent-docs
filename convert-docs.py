#!/usr/bin/env python3
"""
convert-docs.py — gera docs.html a partir de docs/*.md

Fonte única de verdade: docs/*.md. Não edite docs.html diretamente —
rode este script depois de editar qualquer arquivo em docs/.

Uso:
    python3 convert-docs.py

Só usa a biblioteca padrão do Python 3, nenhuma dependência externa.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
TEMPLATE_PATH = ROOT / "docs-template.html"
OUTPUT_PATH = ROOT / "docs.html"

NAV_PLACEHOLDER = "<!-- DOCS_NAV -->"
CONTENT_PLACEHOLDER = "<!-- DOCS_CONTENT -->"

# Ordem de renderização = ordem real da navegação no site
FILES = [
    "getting-started.md",
    "core-concepts.md",
    "database.md",
    "cli.md",
    "utilities.md",
    "deployment.md",
]

# ---------------------------------------------------------------------------
# Tokenizer: markdown -> lista de blocos
# ---------------------------------------------------------------------------

FENCE_RE = re.compile(r"^```(\w*)\s*$")
HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
HR_RE = re.compile(r"^-{3,}\s*$")
UL_ITEM_RE = re.compile(r"^[-*]\s+(.*)$")
OL_ITEM_RE = re.compile(r"^\d+\.\s+(.*)$")


def is_block_start(line):
    s = line.strip()
    if s == "":
        return True
    if HEADING_RE.match(s):
        return True
    if FENCE_RE.match(s):
        return True
    if HR_RE.match(s):
        return True
    if UL_ITEM_RE.match(s):
        return True
    if OL_ITEM_RE.match(s):
        return True
    if s.startswith(">"):
        return True
    if s.startswith("|"):
        return True
    return False


def is_table_separator(line):
    s = line.strip()
    return bool(re.match(r"^\|?[\s:|-]+\|?$", s)) and "-" in s


def split_table_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def tokenize(text):
    lines = text.split("\n")
    i, n = 0, len(lines)
    tokens = []

    while i < n:
        raw = lines[i]
        s = raw.strip()

        if s == "":
            i += 1
            continue

        m = FENCE_RE.match(s)
        if m:
            lang = m.group(1)
            i += 1
            code_lines = []
            while i < n and lines[i].strip() != "```":
                code_lines.append(lines[i])
                i += 1
            i += 1  # pula a cerca de fechamento
            tokens.append(("code", lang, "\n".join(code_lines)))
            continue

        m = HEADING_RE.match(s)
        if m:
            tokens.append(("h", len(m.group(1)), m.group(2).strip()))
            i += 1
            continue

        if HR_RE.match(s):
            tokens.append(("hr",))
            i += 1
            continue

        if s.startswith("|") and i + 1 < n and is_table_separator(lines[i + 1]):
            header = split_table_row(s)
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_table_row(lines[i]))
                i += 1
            tokens.append(("table", header, rows))
            continue

        if s.startswith(">"):
            bq_lines = []
            while i < n and lines[i].strip().startswith(">"):
                bq_lines.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            tokens.append(("blockquote", bq_lines))
            continue

        m = UL_ITEM_RE.match(s)
        if m:
            items = []
            while i < n and UL_ITEM_RE.match(lines[i].strip()):
                items.append(UL_ITEM_RE.match(lines[i].strip()).group(1))
                i += 1
            tokens.append(("ul", items))
            continue

        m = OL_ITEM_RE.match(s)
        if m:
            items = []
            while i < n and OL_ITEM_RE.match(lines[i].strip()):
                items.append(OL_ITEM_RE.match(lines[i].strip()).group(1))
                i += 1
            tokens.append(("ol", items))
            continue

        # parágrafo: acumula até linha em branco ou início de outro bloco
        para = [s]
        i += 1
        while i < n and lines[i].strip() != "" and not is_block_start(lines[i]):
            para.append(lines[i].strip())
            i += 1
        tokens.append(("p", " ".join(para)))

    return tokens


# ---------------------------------------------------------------------------
# Slugify (preserva acentos, bate com os IDs já usados no site)
# ---------------------------------------------------------------------------


def strip_inline_markers(text):
    # remove marcações de código/negrito/itálico/link antes de gerar o slug,
    # mantendo só o texto visível
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text


def slugify(text):
    text = strip_inline_markers(text)
    kept = [ch for ch in text if ch.isalnum() or ch.isspace() or ch == "-"]
    slug = "".join(kept).strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")


# ---------------------------------------------------------------------------
# Inline formatting: markdown -> HTML (aplicado a texto de parágrafo/heading/
# item de lista/célula de tabela/blockquote)
# ---------------------------------------------------------------------------

INLINE_CODE_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def resolve_link(url, anchor_map):
    # /docs/xxx -> âncora da primeira seção (H2) do arquivo xxx nesta página única
    m = re.match(r"^/docs/([a-z-]+)(#.*)?$", url)
    if m:
        key = m.group(1)
        target = anchor_map.get(key)
        if target:
            return "#" + target
    return url


def format_inline(text, anchor_map):
    text = html.escape(text, quote=False)
    text = INLINE_CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = LINK_RE.sub(
        lambda m: f'<a href="{resolve_link(m.group(2), anchor_map)}">{m.group(1)}</a>',
        text,
    )
    text = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    return text


# ---------------------------------------------------------------------------
# Render: tokens -> HTML de seções
# ---------------------------------------------------------------------------


def render_code(lang, raw):
    lang_class = f"language-{lang}" if lang else "language-none"
    escaped = html.escape(raw, quote=False)
    return (
        '<div class="code-block">\n'
        f'    <pre><code class="{lang_class}">{escaped}</code></pre>\n'
        "</div>"
    )


def render_table(header, rows, anchor_map):
    out = ["<table>", "    <thead>", "        <tr>"]
    for cell in header:
        out.append(f"            <th>{format_inline(cell, anchor_map)}</th>")
    out.extend(["        </tr>", "    </thead>", "    <tbody>"])
    for row in rows:
        out.append("        <tr>")
        for cell in row:
            out.append(f"            <td>{format_inline(cell, anchor_map)}</td>")
        out.append("        </tr>")
    out.extend(["    </tbody>", "</table>"])
    return "\n".join(out)


def render_blockquote(lines, anchor_map):
    # separa em parágrafos nas linhas '>' vazias
    paragraphs, current = [], []
    for line in lines:
        if line.strip() == "":
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    body = "\n".join(f"    <p>{format_inline(p, anchor_map)}</p>" for p in paragraphs)
    return f'<div class="note-box">\n{body}\n</div>'


def render_list(tag, items, anchor_map):
    lis = "\n".join(f"    <li>{format_inline(item, anchor_map)}</li>" for item in items)
    return f"<{tag}>\n{lis}\n</{tag}>"


def extract_sections(tokens):
    """1ª passada (sem depender de anchor_map): parte os tokens de UM arquivo
    em [{'id': slug-base, 'heading_text':..., 'body_tokens':[tok,...]}]. H1
    vira só o título de navegação (não vira seção); cada H2 abre uma nova
    seção; H3/H4 ficam como tokens dentro da seção atual pra serem
    renderizados na 2ª passada; texto antes do primeiro H2 é prependido na
    primeira seção em vez de virar uma seção órfã sem título; '---' é
    descartado (cada seção já fecha com <hr> automaticamente)."""
    nav_title = None
    sections = []
    current = None
    preamble = []

    for tok in tokens:
        kind = tok[0]

        if kind == "h":
            level, text = tok[1], tok[2]
            if level == 1:
                nav_title = text
                continue
            if level == 2:
                if current is not None:
                    sections.append(current)
                current = {"id": slugify(text), "heading_text": text, "body_tokens": []}
                if preamble:
                    current["body_tokens"].extend(preamble)
                    preamble = []
                continue
            # h3/h4 viram um token normal dentro do body
            target = current["body_tokens"] if current is not None else preamble
            target.append(tok)
            continue

        if kind == "hr":
            continue

        target = current["body_tokens"] if current is not None else preamble
        target.append(tok)

    if current is not None:
        sections.append(current)
    elif preamble:
        # arquivo sem nenhum H2 (não ocorre nos docs atuais, mas não descarta)
        sections.append({"id": "conteudo", "heading_text": "", "body_tokens": preamble})

    return nav_title, sections


def render_section_body(body_tokens, anchor_map):
    parts = []
    for tok in body_tokens:
        kind = tok[0]
        if kind == "h":
            level, text = tok[1], tok[2]
            tag = "h3" if level == 3 else "h4"
            parts.append(f"<{tag}>{format_inline(text, anchor_map)}</{tag}>")
        elif kind == "code":
            parts.append(render_code(tok[1], tok[2]))
        elif kind == "table":
            parts.append(render_table(tok[1], tok[2], anchor_map))
        elif kind == "blockquote":
            parts.append(render_blockquote(tok[1], anchor_map))
        elif kind == "ul":
            parts.append(render_list("ul", tok[1], anchor_map))
        elif kind == "ol":
            parts.append(render_list("ol", tok[1], anchor_map))
        elif kind == "p":
            parts.append(f"<p>{format_inline(tok[1], anchor_map)}</p>")
    return parts


def assign_unique_ids(files_data):
    """Desambigua ids repetidos entre arquivos (ex.: 'Boas Práticas' aparece
    em database.md, utilities.md e deployment.md). O 1º arquivo (na ordem de
    FILES) a usar um slug fica com ele intacto; ocorrências seguintes ganham
    o nome do arquivo como sufixo, pra nunca colidir e continuar legível."""
    used_ids = set()
    for file_key, nav_title, sections in files_data:
        for sec in sections:
            base = sec["id"]
            if base not in used_ids:
                final_id = base
            else:
                final_id = f"{base}-{file_key}"
                # no caso (bem improvável) de ainda colidir, força unicidade
                n = 2
                while final_id in used_ids:
                    final_id = f"{base}-{file_key}-{n}"
                    n += 1
            used_ids.add(final_id)
            sec["id"] = final_id


def render_file(file_key, nav_title, sections, anchor_map, is_last_file):
    section_htmls = []
    for idx, sec in enumerate(sections):
        is_last_section_overall = is_last_file and idx == len(sections) - 1
        body_parts = render_section_body(sec["body_tokens"], anchor_map)
        heading_html = (
            f'<h2>{format_inline(sec["heading_text"], anchor_map)}</h2>'
            if sec["heading_text"]
            else ""
        )
        body = "\n\n".join(body_parts)
        hr = "" if is_last_section_overall else "\n\n                <hr>\n"
        section_htmls.append(
            f'            <section id="{sec["id"]}" class="doc-section">\n'
            f"                {heading_html}\n\n"
            f"                {body}\n"
            f"{hr}"
            f"            </section>"
        )

    nav_items = "\n".join(
        f'                        <li><a href="#{sec["id"]}">'
        f'{format_inline(sec["heading_text"], anchor_map)}</a></li>'
        for sec in sections
    )
    nav_block = (
        '                <div class="nav-section">\n'
        f"                    <h3>{html.escape(nav_title or file_key, quote=False)}</h3>\n"
        "                    <ul>\n"
        f"{nav_items}\n"
        "                    </ul>\n"
        "                </div>"
    )

    return nav_block, "\n\n".join(section_htmls)


def main():
    # 1ª passada: tokeniza e parte em seções (ids ainda não são únicos
    # globalmente nem HTML-renderizados — isso depende do anchor_map, que só
    # existe depois que os ids finais estiverem prontos)
    files_data = []  # [(file_key, nav_title, sections), ...]
    for filename in FILES:
        text = (DOCS_DIR / filename).read_text(encoding="utf-8")
        tokens = tokenize(text)
        nav_title, sections = extract_sections(tokens)
        file_key = filename[: -len(".md")]
        files_data.append((file_key, nav_title, sections))

    assign_unique_ids(files_data)

    anchor_map = {
        file_key: sections[0]["id"]
        for file_key, _, sections in files_data
        if sections
    }

    # 2ª passada: agora com ids finais e anchor_map completo, renderiza tudo
    nav_blocks = []
    content_blocks = []
    for idx, (file_key, nav_title, sections) in enumerate(files_data):
        is_last = idx == len(files_data) - 1
        nav_block, content_block = render_file(
            file_key, nav_title, sections, anchor_map, is_last
        )
        nav_blocks.append(nav_block)
        content_blocks.append(content_block)

    nav_html = "\n".join(nav_blocks)
    content_html = "\n\n".join(content_blocks)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if NAV_PLACEHOLDER not in template or CONTENT_PLACEHOLDER not in template:
        raise SystemExit(
            f"docs-template.html precisa conter {NAV_PLACEHOLDER!r} e {CONTENT_PLACEHOLDER!r}"
        )

    output = template.replace(NAV_PLACEHOLDER, nav_html).replace(
        CONTENT_PLACEHOLDER, content_html
    )
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"✓ {OUTPUT_PATH.relative_to(ROOT)} gerado a partir de {len(FILES)} arquivos em docs/")


if __name__ == "__main__":
    main()
