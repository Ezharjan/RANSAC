"""
Pieces shared by build_page.py and build_pdf.py.

Both builders turn the same RANSAC_Tutorial.md into a self-contained document,
so the two things markdown cannot express on its own — the flowcharts and the
display maths — are defined here once, and imported by both. That way the HTML
and the PDF can never drift apart.

Nothing here needs editing unless you add new diagrams or new $$...$$ blocks to
the markdown.
"""
import base64
import pathlib

HERE = pathlib.Path(__file__).resolve().parent      # works from any folder, any OS

# The three ```mermaid fences in RANSAC_Tutorial.md, in the order they appear.
# diagrams.py renders each one to dia_<name>.svg with Graphviz.
DIAGRAM_ORDER = ["loop", "pipeline", "taxonomy"]


def load_diagram(name: str) -> str:
    """Return the inline SVG for one diagram. Run diagrams.py first."""
    f = HERE / f"dia_{name}.svg"
    if not f.exists():
        raise SystemExit(
            f"Missing {f.name}. Run:  python diagrams.py\n"
            "(that step needs Graphviz installed and 'dot' on your PATH)"
        )
    return f.read_text(encoding="utf-8")


def figure_data_uri(png: pathlib.Path) -> str:
    """Embed Figure 1 directly in the document so nothing is linked externally."""
    if not png.exists():
        raise SystemExit(f"Missing {png.name}. Run:  python make_figs.py")
    return "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()


def frac(num: str, den: str) -> str:
    """A CSS-only fraction; renders identically in a browser and in WeasyPrint."""
    return (f'<span class="frac"><span class="num">{num}</span>'
            f'<span class="den">{den}</span></span>')


# The six $$...$$ display-maths blocks of RANSAC_Tutorial.md, in document order,
# written as plain HTML. This keeps both outputs free of any JavaScript maths
# renderer, so they work offline and on GitHub Pages with no CDN.
MATH = [
    # 4.1
    'P(sample is all-inlier) &nbsp;=&nbsp; <i>w</i><sup><i>s</i></sup>',

    # 4.2 derivation
    '1 &minus; (1 &minus; <i>w</i><sup><i>s</i></sup>)<sup>N</sup> &nbsp;&ge;&nbsp; <i>p</i>'
    '&nbsp;&nbsp;&nbsp;&hArr;&nbsp;&nbsp;&nbsp;'
    '(1 &minus; <i>w</i><sup><i>s</i></sup>)<sup>N</sup> &nbsp;&le;&nbsp; 1 &minus; <i>p</i>',

    # 4.2 the boxed result
    '<span class="boxed"><i>N</i> &nbsp;&ge;&nbsp; '
    + frac('log(1 &minus; <i>p</i>)', 'log(1 &minus; <i>w</i><sup><i>s</i></sup>)')
    + '</span>',

    # 4.5 hypergeometric probability
    'P(clean) &nbsp;=&nbsp; ' + frac('C(<i>I</i>, <i>s</i>)', 'C(<i>n</i>, <i>s</i>)')
    + ' &nbsp;=&nbsp; <span class="bigop">&prod;</span>'
      '<sub class="lim"><i>j</i>=0</sub><sup class="lim"><i>s</i><sup class="lim">s&minus;1</sup>minus;1</sup> '
    + frac('<i>I</i> &minus; <i>j</i>', '<i>n</i> &minus; <i>j</i>'),

    # 4.5 first-order correction
    frac('P(clean)', '<i>w</i><sup><i>s</i></sup>') + ' &nbsp;&asymp;&nbsp; 1 &minus; '
    + frac('<i>s</i>(<i>s</i> &minus; 1)(1 &minus; <i>w</i>)', '2 <i>w n</i>'),

    # 4.9 cost model
    'Cost &nbsp;=&nbsp; <i>N</i> ( C<sub>solve</sub> + <i>n</i> C<sub>residual</sub> )'
    ' &nbsp;+&nbsp; C<sub>polish</sub>',
]

# Styling for the maths above. Shared so the HTML and the PDF look the same.
MATH_CSS = """
.math { text-align:center; margin:1.1em 0; font-size:1.12em;
        page-break-inside:avoid; }
.frac { display:inline-block; vertical-align:middle; text-align:center;
        margin:0 .25em; }
.frac .num { display:block; border-bottom:1px solid currentColor; padding:0 .35em; }
.frac .den { display:block; padding:0 .35em; }
.boxed { display:inline-block; border:1px solid var(--accent, #1f6fb2);
         border-radius:4px; padding:.3em .9em;
         background:var(--surface-2, #f4f8fc); }
.bigop { font-size:1.5em; vertical-align:middle; }
sub.lim, sup.lim { font-size:.62em; }
"""
