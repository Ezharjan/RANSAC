# RANSAC — From Greenhand to Expert

A complete, verified tutorial on **RAN**dom **SA**mple **C**onsensus: the theory, the mathematics,
a from-scratch implementation, the modern library toolbox, the failure modes, and the 2026 state
of the art.

Every code block in the tutorial was executed before publication, every number in every table was
computed rather than recalled, and every reference was checked against its primary source.

📖 **Read it online:** [https://ezharjan.github.io/RANSAC/](https://ezharjan.github.io/RANSAC/)

---

## Contents

- [Three ways to read it](#three-ways-to-read-it)
- [Repository layout](#repository-layout)
- [Quick start](#quick-start)
- [Script reference](#script-reference) ← *how to use every script*
- [Using the RANSAC engine in your own code](#using-the-ransac-engine-in-your-own-code)
- [Installing the prerequisites](#installing-the-prerequisites)
- [Troubleshooting](#troubleshooting)
- [GitHub Pages notes](#github-pages-notes)
- [What is inside the tutorial](#what-is-inside-the-tutorial)

---

## Three ways to read it

| Format | File | Best for |
|---|---|---|
| **Web page** | `index.html` | Reading on screen. Self-contained — double-click to open, no internet needed. Adapts to light/dark mode. This is what GitHub Pages serves. |
| **PDF** | `RANSAC_Tutorial.pdf` | Printing, annotating, offline reading. 44 pages, A4. |
| **Markdown** | `RANSAC_Tutorial.md` | Editing the text, or reading directly in GitHub's file browser. |

All three contain identical content. `RANSAC_Tutorial.md` is the single source of truth — the
other two are generated from it.

---

## Repository layout

### Documents — what you read

| File | Size | Description |
|---|---|---|
| `index.html` | ~740 KB | The tutorial as a web page. |
| `RANSAC_Tutorial.pdf` | ~730 KB | The tutorial as a 44-page print document. |
| `RANSAC_Tutorial.md` | ~100 KB | **The source text.** Edit this, then rebuild. |
| `ransac_figures.png` | ~375 KB | Figure 1 — the four-panel summary of RANSAC's behaviour. |
| `dia_loop.svg`<br>`dia_pipeline.svg`<br>`dia_taxonomy.svg` | ~38 KB total | The three flowcharts, rendered by Graphviz. Committed so the page can be rebuilt without installing Graphviz. |

### Code — what you run

| File | Needs | Description |
|---|---|---|
| `ransac_from_scratch.py` | NumPy | **The main code deliverable.** A ~120-line RANSAC engine plus line, circle and plane models. Run it for a demo, or import it into your own project. |
| `make_figs.py` | NumPy, Matplotlib | Regenerates `ransac_figures.png`. |
| `diagrams.py` | Graphviz | Regenerates `dia_*.svg`. |
| `common.py` | — | Shared definitions imported by both builders. Not run directly. |
| `build_page.py` | markdown, pygments | `RANSAC_Tutorial.md` → `index.html` |
| `build_pdf.py` | markdown, pygments, WeasyPrint | `RANSAC_Tutorial.md` → `RANSAC_Tutorial.pdf` |

### Repository housekeeping

| File | Purpose |
|---|---|
| `README.md` | This file. |
| `requirements.txt` | Python dependencies — `pip install -r requirements.txt`. |
| `.gitignore` | Keeps caches and build intermediates out of the repository. |
| `.nojekyll` | Tells GitHub Pages to serve files as-is rather than running Jekyll. Empty on purpose — do not delete it. |

**You only need the build scripts if you intend to edit the tutorial text.** To read the tutorial
or to use the RANSAC engine, ignore them entirely.

---

## Quick start

```bash
# See RANSAC working, in 10 seconds
pip install numpy
python ransac_from_scratch.py
```

```bash
# Edit the text and rebuild the web page
pip install markdown pygments
# ...edit RANSAC_Tutorial.md...
python build_page.py
```

---

## Script reference

Every script resolves its paths relative to **its own location**, so you can run it from any
working directory and on any operating system. There is nothing to configure.

---

### `ransac_from_scratch.py` — the RANSAC engine

The one file you would actually reuse. Pure NumPy, no hard-coded paths, no other project files
required. Copy it anywhere.

```bash
python ransac_from_scratch.py
```

| | |
|---|---|
| **Reads** | nothing |
| **Writes** | nothing (prints to the terminal) |
| **Requires** | `numpy` |
| **Runtime** | under 1 second |

Running it directly fits a line at 40 % outliers, a circle at 50 %, and a plane at 60 %, printing
the recovered parameters beside the ground truth:

```text
LINE [ransac] slope=+0.5982 (true +0.6000)  intercept=-4.0139 (true -4.0000)  trials= 10
              inliers=123  precision=0.976  recall=1.000  sigma_hat=0.229
LINE [OLS   ] slope=+0.3192 (true +0.6000)  intercept=-2.8339 (true -4.0000)
              <-- destroyed by outliers
CIRCLE        centre=(+2.996,-1.981) r=5.000  (true (+3.0,-2.0) r=5.0)  trials=36  inliers=103
PLANE         normal=[0.186 -0.281 0.942] d=-1.502  (true [0.188 -0.282 0.941] d=-1.500)
              angle_err=0.147 deg  trials=65  inliers=124
```

Those numbers are deterministic — the demo seeds its random generators, so you should see exactly
this output. See [the API section](#using-the-ransac-engine-in-your-own-code) for how to use it on
your own data.

---

### `make_figs.py` — regenerate Figure 1

```bash
python make_figs.py
```

| | |
|---|---|
| **Reads** | nothing |
| **Writes** | `ransac_figures.png` (overwrites) |
| **Requires** | `numpy`, `matplotlib` |
| **Runtime** | about 3 seconds |

Produces the four-panel figure: (A) RANSAC versus least squares at 40 % outliers, (B) required
trials versus inlier ratio, (C) the threshold sweep, (D) adaptive termination in action.

It also *is* the reference implementation of those four experiments. To change one, edit the
constants near the top of the data section — `M_TRUE`, `B_TRUE`, `SIGMA`, `NI`, `NO`.

**Run this only if you change a figure.** The committed PNG is already correct, and rebuilding it
is not needed for a text edit.

---

### `diagrams.py` — regenerate the flowcharts

```bash
python diagrams.py
```

| | |
|---|---|
| **Reads** | nothing — the diagrams are defined inline, as Graphviz DOT source |
| **Writes** | `dia_loop.svg`, `dia_pipeline.svg`, `dia_taxonomy.svg` (overwrites) |
| **Requires** | **Graphviz** — the `dot` command must be on your `PATH` |
| **Runtime** | under 1 second |

The three diagrams correspond, in order, to the three Mermaid blocks in `RANSAC_Tutorial.md`: the
RANSAC loop (§3.3), the image-matching pipeline (§7.3), and the variant taxonomy (§9). To change
one, edit the `LOOP`, `PIPELINE` or `TAXONOMY` string in this file.

**You rarely need to run this.** The SVGs are committed, so both builders work on a fresh clone
with no Graphviz installed. Run it only if you edit a diagram — or if you add a fourth one, in
which case also add its name to `DIAGRAM_ORDER` in `common.py`.

---

### `build_page.py` — build the web page

```bash
python build_page.py
```

| | |
|---|---|
| **Reads** | `RANSAC_Tutorial.md`, `ransac_figures.png`, `dia_*.svg`, `common.py` |
| **Writes** | `index.html` (overwrites) |
| **Requires** | `markdown`, `pygments` |
| **Runtime** | about 1 second |

This is the script you will use most: edit the markdown, run it, refresh the browser.

It embeds the figure as a data URI and the diagrams as inline SVG, and writes the mathematics as
plain HTML, so the result has **no external dependencies at all** — it works offline, from a
`file://` URL, and on GitHub Pages without any CDN.

On success it prints a self-check worth glancing at:

```text
wrote .../index.html 750 KB
diagrams embedded: 3
tables: 36
maths blocks: 6
unresolved placeholders: 0      <-- must be 0
```

> **⚠️ Running this will overwrite your current `index.html`, and the diagrams will change.**
>
> The `index.html` you deployed came from an earlier version of this script, which emitted
> `<pre class="mermaid">` blocks and relied on the page host to draw them. GitHub Pages has no
> Mermaid renderer, so on your live site those three flowcharts are very likely showing as raw
> `flowchart TD / A[...] --> B[...]` text. Worth checking §3.3, §7.3 and §9 of the deployed page.
>
> This version fixes that by embedding the Graphviz SVGs directly, so no renderer is needed
> anywhere. If you would rather keep your current file exactly as it is, simply don't run this
> script — nothing else in the repository touches `index.html`.

---

### `build_pdf.py` — build the PDF

```bash
python build_pdf.py
```

| | |
|---|---|
| **Reads** | `RANSAC_Tutorial.md`, `ransac_figures.png`, `dia_*.svg`, `common.py` |
| **Writes** | `RANSAC_Tutorial.pdf` (overwrites), `_print.html` (intermediate, git-ignored) |
| **Requires** | `markdown`, `pygments`, `weasyprint` **plus system GTK libraries** |
| **Runtime** | about 7 seconds |

WeasyPrint cannot run JavaScript, which is precisely why the diagrams and mathematics are
pre-rendered rather than drawn in the browser — the same inputs then produce both outputs.

It layers print-specific styling on top: A4 page setup, page numbers, a page break before each
Part, and `page-break-inside: avoid` on tables, code blocks and figures.

**WeasyPrint is the fiddliest dependency here, especially on Windows.** If you would rather not
install it, open `index.html` in a browser and press <kbd>Ctrl</kbd>+<kbd>P</kbd> → *Save as PDF*.
The result is very close and needs nothing extra.

---

### `common.py` — shared definitions

Not run directly. Imported by both builders so the HTML and the PDF can never drift apart.

| Name | What it is |
|---|---|
| `DIAGRAM_ORDER` | The diagram names, in the order the Mermaid blocks appear in the markdown. |
| `load_diagram(name)` | Loads one `dia_*.svg`, with a helpful error if you haven't run `diagrams.py`. |
| `figure_data_uri(png)` | Base64-encodes Figure 1 for inline embedding. |
| `MATH` | The six `$$...$$` display-mathematics blocks, written out as plain HTML. |
| `frac()`, `MATH_CSS` | A CSS-only fraction that renders identically in a browser and in WeasyPrint. |

**If you add a `$$...$$` block to the markdown, add its HTML to `MATH` in document order.** Both
builders substitute the entries sequentially, so a mismatch raises `StopIteration`. The same
applies to a new Mermaid block and `DIAGRAM_ORDER`.

---

### Build order

```
                        ┌─ diagrams.py  ──→ dia_*.svg ────┐
                        │  (needs Graphviz, rarely run)   │
                        │                                 ├─→ build_page.py ─→ index.html
                        ├─ make_figs.py ──→ *.png ────────┤
                        │  (rarely run)                   ├─→ build_pdf.py  ─→ *.pdf
   RANSAC_Tutorial.md ──┴─────────────────────────────────┘
                                                    common.py
```

Full rebuild from scratch:

```bash
python diagrams.py && python make_figs.py && python build_page.py && python build_pdf.py
```

For a text-only edit, **`python build_page.py` alone is enough.**

---

## Using the RANSAC engine in your own code

```python
from ransac_from_scratch import ransac, fit_line, line_residuals, line_to_slope_intercept

result = ransac(
    my_points,                  # (n, 2) array — one datum per row
    fit_line,                   # fit(sample) -> model, or None if degenerate
    line_residuals,             # residuals(model, data) -> (n,) distances
    min_samples=2,              # s — the minimal sample size for this model
    threshold=1.2,              # t — about 2-3x your measurement noise
    refit=fit_line,             # polish on all inliers — do not omit this
)

print(result.model)             # the fitted model
print(result.inliers)           # boolean mask over your data
print(result.inlier_ratio)      # fraction of the data that agreed
print(result.n_trials)          # how many hypotheses it actually needed
print(result.residual_scale)    # robust sigma estimate from the inliers
```

### Fitting a different model

The engine knows nothing about geometry. Supply two functions and a sample size:

```python
def fit_mymodel(sample):
    """sample: (s, ...) array. Return a model, or None if the sample is degenerate."""
    ...

def mymodel_residuals(model, data):
    """Return an (n,) array of non-negative, geometrically meaningful distances."""
    ...

result = ransac(data, fit_mymodel, mymodel_residuals,
                min_samples=s, threshold=t, refit=fit_mymodel)
```

`fit_circle` and `fit_plane` in `ransac_from_scratch.py` are worked examples. Two rules matter:
`fit` must handle **both** the minimal case and the over-determined case, so it can double as
`refit`; and it must return `None` for a degenerate sample rather than crashing.

### Optional arguments

| Argument | Default | Meaning |
|---|---|---|
| `max_trials` | `10_000` | Hard cap. Always keep one. |
| `confidence` | `0.99` | `p` — probability of drawing at least one uncontaminated sample. |
| `score` | `"msac"` | `"msac"` (truncated L2) or `"ransac"` (inlier count). MSAC is ~3× more accurate when the threshold is imperfect. |
| `is_sample_valid` | `None` | Cheap pre-check on a drawn sample, for your own degeneracy tests. |
| `rng` | `None` | Seed or `np.random.Generator`, for reproducible runs. |

**The one parameter that matters is `threshold`.** Set it to roughly 2–3× your measurement noise.
§4.8 of the tutorial derives this from the chi-squared distribution and measures exactly what goes
wrong when you get it wrong.

---

## Installing the prerequisites

```bash
pip install -r requirements.txt
```

Two dependencies cannot be installed with pip:

### Graphviz — only for `diagrams.py`

| Platform | Install |
|---|---|
| Windows | Installer from [graphviz.org/download](https://graphviz.org/download/). Tick **"Add Graphviz to the system PATH"**, then reopen your terminal. |
| macOS | `brew install graphviz` |
| Debian/Ubuntu | `sudo apt install graphviz` |

Verify with `dot -V`. Because `dia_*.svg` is committed, you only need this if you edit a diagram.

### GTK libraries — only for `build_pdf.py`

| Platform | Install |
|---|---|
| Windows | Follow WeasyPrint's [installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) — it needs the GTK3 runtime. |
| macOS | `brew install pango` |
| Debian/Ubuntu | `sudo apt install libpango-1.0-0 libpangoft2-1.0-0` |

Or skip it entirely and print `index.html` to PDF from your browser.

---

## Troubleshooting

| Message | Cause | Fix |
|---|---|---|
| `Missing dia_loop.svg. Run: python diagrams.py` | The SVGs aren't present | Run `python diagrams.py` (needs Graphviz), or restore them with `git checkout dia_loop.svg dia_pipeline.svg dia_taxonomy.svg` |
| `Missing ransac_figures.png. Run: python make_figs.py` | The figure isn't present | `python make_figs.py`, or `git checkout ransac_figures.png` |
| `'dot' is not recognized` / `FileNotFoundError: 'dot'` | Graphviz not on `PATH` | Reinstall with the PATH option ticked, then reopen the terminal |
| `cannot load library 'libgobject-2.0-0'` | WeasyPrint's GTK libraries are missing | See above, or use the browser's *Save as PDF* |
| `StopIteration` in a builder | You added a `$$...$$` or Mermaid block without a matching entry in `common.py` | Add it to `MATH` or `DIAGRAM_ORDER` |
| `unresolved placeholders: 3` (not 0) | A substitution failed | Check that the Figure 1 image line in the markdown is unedited |
| `ModuleNotFoundError: No module named 'common'` | Running a builder with an unusual `sys.path` | `cd` into the repository folder first |

---

## GitHub Pages notes

Already configured — `index.html` sits at the repository root and is self-contained.

Settings → Pages → Source: **Deploy from a branch** → branch `main`, folder `/ (root)`.

- `.nojekyll` stops GitHub from running the files through Jekyll. It is empty on purpose. If your
  download tool skipped it (it is a hidden, zero-byte file), recreate it with `type nul > .nojekyll`
  on Windows, or `touch .nojekyll` elsewhere.
- The PDF is served too, at `https://<your-username>.github.io/<your-repo>/RANSAC_Tutorial.pdf`.
- `RANSAC_Tutorial.md` renders correctly in GitHub's file browser, because its image reference is a
  relative path to a file in the same folder. GitHub also draws the three Mermaid blocks natively
  in that view — so the markdown page shows the diagrams even where a served HTML page would not.
- Repository size is about 2 MB. No Git LFS needed.
- `index.html` is mostly base64 image data, so **every rebuild produces a large diff**. If you edit
  often, consider committing the regenerated page in batches.

---

## What is inside the tutorial

| Part | Title | For you if… |
|---|---|---|
| I | Why RANSAC exists | you have never used it |
| II | The algorithm | you want to *understand* it, not just call it |
| III | The mathematics | you want to defend your parameter choices |
| IV | Build it yourself | you learn by writing code |
| V | The library toolbox | you have a deadline |
| VI | Geometric vision | you work with images or point clouds |
| VII | Failure modes | your RANSAC "works, except sometimes" |
| VIII | The variant zoo | you want the 2026 state of the art |
| IX | Neighbours & alternatives | you want to know when *not* to use it |
| X | Advanced topics | you fit multiple models, or want to learn the sampler |
| XI | Tuning playbook | you want a one-page cheat sheet |
| XII | Exercises | you want to check you really got it |

Plus 39 primary references and a glossary.

### The tutorial in eight sentences

**RANSAC** = **RAN**dom **SA**mple **C**onsensus, Fischler & Bolles, 1981.
It is a *meta-algorithm*: you supply a minimal solver, a residual function and a threshold.
It repeatedly fits a **minimal** sample and keeps the model with the best-supported **consensus set**.
Always use the minimal sample size — smaller samples are exponentially more likely to be clean.
`N = log(1−p) / log(1−wˢ)` trials suffice — remarkably, the dataset size `n` barely enters.
That budget guarantees a clean sample was *drawn*, not that the answer is *right* — so validate.
The threshold is the one parameter that matters: use `2–3 σ`, or MAGSAC++ if you cannot know `σ`.
Then always refit on all the inliers — and if it is too slow, raise `w`, don't tune RANSAC.

---

## License

No license file is included. Add one before making the repository public if you want others to
reuse the material — [choosealicense.com](https://choosealicense.com/) is a good starting point,
and MIT for the code with CC BY 4.0 for the prose is a common pairing.

All papers, libraries and documentation cited in the tutorial remain the property of their
respective authors, and are referenced rather than reproduced.
