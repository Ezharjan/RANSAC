"""Render RANSAC_Tutorial.md into one self-contained, theme-aware HTML page.

Output is index.html, with the figure, the three flowcharts and all maths
embedded inline. It has no external dependencies at all, so it works offline
and on GitHub Pages without any CDN.

Prerequisites:  python diagrams.py   (once, to produce dia_*.svg)
"""
import pathlib
import re

import markdown

from common import DIAGRAM_ORDER, MATH, MATH_CSS, figure_data_uri, load_diagram

HERE = pathlib.Path(__file__).resolve().parent   # works from any folder, any OS
SRC = HERE / "RANSAC_Tutorial.md"
PNG = HERE / "ransac_figures.png"
OUT = HERE / "index.html"        # named for GitHub Pages; rename freely

text = SRC.read_text()

# ------------------------------------------------------------------ figure
text = text.replace(
    "![Figure 1 — RANSAC: what it does, how long it takes, and how to tune it]"
    "(ransac_figures.png)",
    '<p class="fig"><img alt="Figure 1 — RANSAC: what it does, how long it '
    f'takes, and how to tune it" src="{figure_data_uri(PNG)}"></p>',
)
text = text.replace(
    "Figure 1 ships alongside this document as\n`ransac_figures.png`, and §4.4 "
    "contains the script that regenerates it.",
    "Figure 1 is embedded below, and §4.4 contains the script that regenerates it.",
)

# ------------------------------------------------- shield mermaid + math
vault = {}


def stash(html: str) -> str:
    key = f"@@VAULT{len(vault)}@@"
    vault[key] = html
    return key


# mermaid fences -> the Graphviz SVGs from diagrams.py.
# (A <pre class="mermaid"> block would stay raw text on GitHub Pages.)
_d = iter(DIAGRAM_ORDER)
text = re.sub(
    r"```mermaid\n.*?\n```",
    lambda m: (lambda n: stash(f'<div class="dia dia-{n}">{load_diagram(n)}</div>'))(next(_d)),
    text, flags=re.S,
)

# $$...$$ -> plain HTML from common.MATH, so no maths CDN is needed
_m = iter(MATH)
text = re.sub(r"\$\$.+?\$\$",
              lambda m: stash(f'<div class="math">{next(_m)}</div>'),
              text, flags=re.S)

# let the solutions block contain markdown
text = text.replace("<details>", '<details markdown="1">')

# ------------------------------------------------------------------ render
body = markdown.markdown(
    text,
    extensions=["extra", "tables", "fenced_code", "codehilite", "toc", "sane_lists"],
    extension_configs={
        "codehilite": {"guess_lang": False, "noclasses": False},
        "toc": {"permalink": False},
    },
)
for key, html in vault.items():
    body = body.replace(f"<p>{key}</p>", html).replace(key, html)

# markdown leaves "[ ]" as literal text; turn it into a real checkbox
body = body.replace('<li>[ ] ',
                    '<li class="task"><input type="checkbox" disabled> ')

# ------------------------------------------------------------------ styling
from pygments.formatters import HtmlFormatter  # noqa: E402

pyg_light = HtmlFormatter(style="friendly").get_style_defs(".codehilite")
pyg_dark_media = HtmlFormatter(style="github-dark").get_style_defs(
    ':root:not([data-theme="light"]) .codehilite')
pyg_dark_attr = HtmlFormatter(style="github-dark").get_style_defs(
    ':root[data-theme="dark"] .codehilite')

CSS = """
:root{
  --bg:#fbfaf8; --surface:#ffffff; --surface-2:#f4f2ee; --text:#1c1b19;
  --muted:#6b6660; --rule:#e2ded7; --accent:#1f6fb2; --accent-2:#0b8a3d;
  --warn:#cc3311; --code-bg:#f6f4f0; --shadow:0 1px 3px rgba(0,0,0,.06);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#16181c; --surface:#1d2025; --surface-2:#23272e; --text:#e6e3de;
    --muted:#9a948c; --rule:#31363e; --accent:#63a9e0; --accent-2:#5cc98a;
    --warn:#ef7a63; --code-bg:#1a1d22; --shadow:0 1px 3px rgba(0,0,0,.4);
  }
}
:root[data-theme="dark"]{
  --bg:#16181c; --surface:#1d2025; --surface-2:#23272e; --text:#e6e3de;
  --muted:#9a948c; --rule:#31363e; --accent:#63a9e0; --accent-2:#5cc98a;
  --warn:#ef7a63; --code-bg:#1a1d22; --shadow:0 1px 3px rgba(0,0,0,.4);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--text);
  font-family:"Charter","Iowan Old Style","Palatino Linotype",Palatino,
              Georgia,"Times New Roman",serif;
  font-size:17px; line-height:1.62;
}
.wrap{max-width:53rem; margin:0 auto; padding:2.6rem 1.25rem 6rem}
@media (max-width:640px){ body{font-size:16px} .wrap{padding:1.5rem 1rem 4rem} }

h1,h2,h3{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
              "Helvetica Neue",Arial,sans-serif;
  line-height:1.22; letter-spacing:-.011em;
}
h1{font-size:2.15rem; margin:.2em 0 .1em; font-weight:800}
h1+h3{color:var(--muted); font-weight:500; font-size:1.12rem;
      margin:0 0 1.6rem; letter-spacing:0}
h1:not(:first-of-type){
  margin-top:3.6rem; padding-top:1.5rem; border-top:3px solid var(--accent);
  font-size:1.85rem;
}
h2{font-size:1.32rem; margin:2.5rem 0 .7rem; font-weight:700}
h3{font-size:1.08rem; margin:2rem 0 .5rem; font-weight:700}
h1 code,h2 code,h3 code{font-size:.9em}

p{margin:0 0 1.05rem}
a{color:var(--accent); text-decoration:none; border-bottom:1px solid transparent}
a:hover{border-bottom-color:var(--accent)}
hr{border:0; border-top:1px solid var(--rule); margin:2.6rem 0}
strong{font-weight:700}
blockquote{
  margin:1.3rem 0; padding:.8rem 1.1rem; background:var(--surface-2);
  border-left:4px solid var(--accent); border-radius:0 6px 6px 0;
}
blockquote p:last-child{margin:0}
ul,ol{padding-left:1.35rem; margin:0 0 1.05rem}
li{margin:.3rem 0}
li input[type=checkbox]{margin-right:.45rem}

code,kbd,samp{
  font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,
              "Liberation Mono",monospace;
  font-size:.875em;
}
:not(pre)>code{
  background:var(--code-bg); border:1px solid var(--rule);
  padding:.1em .34em; border-radius:4px; white-space:nowrap;
}
pre{
  background:var(--code-bg); border:1px solid var(--rule); border-radius:8px;
  padding:.95rem 1.1rem; overflow-x:auto; margin:1.2rem 0;
  font-size:.83rem; line-height:1.55; box-shadow:var(--shadow);
}
pre code{background:none; border:0; padding:0; white-space:pre}
.codehilite{background:none}

.tbl{overflow-x:auto; margin:1.3rem 0; -webkit-overflow-scrolling:touch}
table{border-collapse:collapse; width:100%; font-size:.86rem;
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
th,td{border:1px solid var(--rule); padding:.46rem .62rem;
      text-align:left; vertical-align:top}
th{background:var(--surface-2); font-weight:700; white-space:nowrap}
tbody tr:nth-child(even){background:color-mix(in srgb,var(--surface-2) 45%,transparent)}
td code,th code{white-space:normal}

.fig{margin:1.6rem 0}
.fig img{max-width:100%; height:auto; display:block;
         border:1px solid var(--rule); border-radius:8px;
         background:#fff; box-shadow:var(--shadow)}

.dia{
  margin:1.6rem 0; text-align:center; overflow-x:auto;
  -webkit-overflow-scrolling:touch;
}
.dia svg{max-width:100%; height:auto}
/* the taxonomy chart is very wide: let it scroll rather than shrink to nothing */
.dia-taxonomy{padding-bottom:.4rem}
.dia-taxonomy svg{max-width:none; min-width:900px}
@media (min-width:1100px){ .dia-taxonomy svg{min-width:0; max-width:100%} }
/* Graphviz emits black strokes/text; retint them for dark mode */
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]) .dia svg text{fill:#e6e3de}
  :root:not([data-theme="light"]) .dia{background:#f7f6f3; border-radius:8px; padding:.7rem 0}
}
:root[data-theme="dark"] .dia{background:#f7f6f3; border-radius:8px; padding:.7rem 0}

details{
  margin:1.5rem 0; padding:.85rem 1.15rem; background:var(--surface-2);
  border:1px solid var(--rule); border-radius:8px;
}
details summary{cursor:pointer; font-weight:700; font-family:-apple-system,
  BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
details[open] summary{margin-bottom:.8rem; padding-bottom:.5rem;
  border-bottom:1px solid var(--rule)}

div[align=center]{
  margin-top:3rem; padding:1.6rem 1.2rem; background:var(--surface-2);
  border:1px solid var(--rule); border-radius:10px;
}
div[align=center] h3{margin-top:0}
"""
CSS += MATH_CSS

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RANSAC — From Greenhand to Expert</title>
<style>
{CSS}
li.task{{list-style:none; margin-left:-1.1rem}}
{pyg_light}
@media (prefers-color-scheme: dark){{
{pyg_dark_media}
}}
{pyg_dark_attr}
</style>
</head>
<body>
<main class="wrap">
{body}
</main>
<script>
// wrap tables so wide ones scroll inside themselves, never the page body
document.querySelectorAll('table').forEach(function (t) {{
  if (t.parentElement && t.parentElement.classList.contains('tbl')) return;
  var d = document.createElement('div'); d.className = 'tbl';
  t.parentNode.insertBefore(d, t); d.appendChild(t);
}});
</script>
</body>
</html>
"""

OUT.write_text(HTML)
print("wrote", OUT, OUT.stat().st_size // 1024, "KB")
print("diagrams embedded:", HTML.count('class="dia '))
print("tables:", HTML.count("<table>"))
print("maths blocks:", HTML.count('class="math"'))
print("unresolved placeholders:", HTML.count("@@VAULT"))
