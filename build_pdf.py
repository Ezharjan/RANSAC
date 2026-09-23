"""Render RANSAC_Tutorial.md to a print-ready PDF (WeasyPrint has no JS,
so Mermaid diagrams are pre-rendered with Graphviz and the six display-math
expressions are written out as HTML)."""
import pathlib
import re

import markdown
from pygments.formatters import HtmlFormatter
from weasyprint import HTML

from common import DIAGRAM_ORDER, MATH, figure_data_uri, load_diagram

HERE = pathlib.Path(__file__).resolve().parent   # works from any folder, any OS
SRC = HERE / "RANSAC_Tutorial.md"
PNG = HERE / "ransac_figures.png"
OUT = HERE / "RANSAC_Tutorial.pdf"

text = SRC.read_text(encoding="utf-8")


vault = {}


def stash(html):
    k = f"@@V{len(vault)}@@"
    vault[k] = html
    return k


# figure -> inline data URI
text = text.replace(
    "![Figure 1 — RANSAC: what it does, how long it takes, and how to tune it]"
    "(ransac_figures.png)",
    stash('<div class="fig"><img alt="Figure 1 — RANSAC: what it does, how long it '
          f'takes, and how to tune it" src="{figure_data_uri(PNG)}"></div>'),
)

# mermaid -> pre-rendered Graphviz SVG, in document order
_d = iter(DIAGRAM_ORDER)
text = re.sub(
    r"```mermaid\n.*?\n```",
    lambda m: (lambda n: stash(f'<div class="dia dia-{n}">{load_diagram(n)}</div>'))(next(_d)),
    text, flags=re.S,
)

# display math -> hand-written HTML, in document order
_m = iter(MATH)
text = re.sub(r"\$\$.+?\$\$",
              lambda m: stash(f'<div class="math">{next(_m)}</div>'),
              text, flags=re.S)
text = text.replace("<details>", '<details markdown="1" open>')
text = text.replace('<div align="center">', '<div align="center" markdown="1">')

body = markdown.markdown(
    text,
    # "toc" gives every heading an id, so the §-links inside the PDF resolve
    extensions=["extra", "tables", "fenced_code", "codehilite", "toc", "sane_lists"],
    extension_configs={"codehilite": {"guess_lang": False},
                       "toc": {"permalink": False}},
)
for k, v in vault.items():
    body = body.replace(f"<p>{k}</p>", v).replace(k, v)
body = body.replace('<li>[ ] ', '<li class="task">☐ ')

CSS = """
@page {
  size: A4; margin: 19mm 17mm 20mm 17mm;
  @bottom-center { content: counter(page); font-family: Helvetica, sans-serif;
                   font-size: 8.5pt; color: #888; }
}
@page :first { @bottom-center { content: ""; } }

body { font-family: "DejaVu Serif", Georgia, serif; font-size: 9.6pt;
       line-height: 1.48; color: #1c1b19; }
h1, h2, h3 { font-family: "DejaVu Sans", Helvetica, sans-serif;
             line-height: 1.2; page-break-after: avoid; }
h1 { font-size: 19pt; font-weight: 700; margin: 0 0 .2em; }
h1 + h3 { color: #6b6660; font-weight: 400; font-size: 11.5pt; margin: 0 0 1.4em; }
h1:not(:first-of-type) { font-size: 16pt; page-break-before: always;
  padding-top: 0; margin-top: 0; padding-bottom: .25em;
  border-bottom: 2.5pt solid #1f6fb2; }
h2 { font-size: 11.6pt; margin: 1.5em 0 .5em; font-weight: 700; }
h3 { font-size: 10.2pt; margin: 1.2em 0 .4em; font-weight: 700; }
p  { margin: 0 0 .62em; orphans: 3; widows: 3; }
a  { color: #14518a; text-decoration: none; }
hr { border: 0; border-top: .5pt solid #ddd; margin: 1.2em 0; }
ul, ol { padding-left: 1.2em; margin: 0 0 .62em; }
li { margin: .16em 0; }
li.task { list-style: none; margin-left: -1em; }
blockquote { margin: .8em 0; padding: .5em .8em; background: #f4f2ee;
             border-left: 2.5pt solid #1f6fb2; page-break-inside: avoid; }
blockquote p:last-child { margin: 0; }

code, kbd { font-family: "DejaVu Sans Mono", monospace; font-size: .84em; }
:not(pre) > code { background: #f4f2ee; border: .4pt solid #e0dcd5;
                   padding: 0 .22em; border-radius: 2pt; }
pre { background: #f7f5f1; border: .5pt solid #e0dcd5; border-radius: 3pt;
      padding: .5em .7em; font-size: 7.3pt; line-height: 1.38;
      white-space: pre-wrap; word-wrap: break-word; page-break-inside: avoid;
      margin: .7em 0; }
pre code { background: none; border: 0; padding: 0; }

table { border-collapse: collapse; width: 100%; font-size: 7.8pt;
        font-family: "DejaVu Sans", Helvetica, sans-serif;
        margin: .8em 0; page-break-inside: avoid; }
th, td { border: .4pt solid #d8d4cd; padding: 2.6pt 4pt; text-align: left;
         vertical-align: top; }
th { background: #f0eeea; font-weight: 700; }
tbody tr:nth-child(even) { background: #faf9f7; }
td code, th code { font-size: .95em; }

.fig { margin: 1em 0; page-break-inside: avoid; text-align: center; }
.fig img { max-width: 100%; border: .5pt solid #ddd; }
.dia { margin: 1em 0; text-align: center; page-break-inside: avoid; }
.dia svg { max-width: 100%; height: auto; }
.dia-loop svg { max-height: 215mm; }
.dia-taxonomy svg { max-width: 100%; }

.math { text-align: center; margin: .9em 0; font-size: 11pt;
        font-family: "DejaVu Serif", Georgia, serif; page-break-inside: avoid; }
.frac { display: inline-block; vertical-align: middle; text-align: center;
        margin: 0 .25em; }
.frac .num { display: block; border-bottom: .7pt solid #1c1b19; padding: 0 .35em; }
.frac .den { display: block; padding: 0 .35em; }
.boxed { display: inline-block; border: 1pt solid #1f6fb2; border-radius: 3pt;
         padding: .3em .9em; background: #f4f8fc; }
.bigop { font-size: 1.5em; vertical-align: middle; }
sub.lim, sup.lim { font-size: .62em; }

details { margin: .9em 0; padding: .6em .8em; background: #f7f5f1;
          border: .5pt solid #e0dcd5; border-radius: 3pt; }
details summary { font-weight: 700; font-family: "DejaVu Sans", sans-serif;
                  margin-bottom: .5em; }
div[align=center] { margin-top: 1.4em; padding: 1em; background: #f4f2ee;
                    border: .5pt solid #e0dcd5; border-radius: 4pt;
                    page-break-inside: avoid; }
div[align=center] h3 { margin-top: 0; }
"""

html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>RANSAC — From Greenhand to Expert</title>
<style>{CSS}
{HtmlFormatter(style="friendly").get_style_defs(".codehilite")}</style>
</head><body>{body}</body></html>"""

HTML(string=html, base_url=str(HERE)).write_pdf(str(OUT))
print("wrote", OUT, OUT.stat().st_size // 1024, "KB")
