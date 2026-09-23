"""Render the three tutorial flowcharts to SVG with Graphviz.

The SVGs are embedded by both build_page.py and build_pdf.py.
Usage:  python diagrams.py      (needs Graphviz: the `dot` command on PATH)
"""
import subprocess, pathlib

HERE = pathlib.Path(__file__).resolve().parent   # works from any folder, any OS

BLUE, GREEN, RED, PURPLE = "#1f6fb2", "#0b8a3d", "#cc3311", "#8a5fb0"
BLUE_F, GREEN_F, RED_F, PURPLE_F = "#e8f0f8", "#eaf5ec", "#fdeeea", "#f4eef8"

LOOP = f'''
digraph ransac_loop {{
  rankdir=TB; bgcolor="transparent"; nodesep=0.45; ranksep=0.40;
  node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=11
        fillcolor="white" color="#3a3a3a" penwidth=1.2 margin="0.16,0.09"];
  edge [fontname="Helvetica" fontsize=9 color="#555555" arrowsize=0.7];

  A [label="Data X: n points\\nunknown inlier ratio w" fillcolor="{BLUE_F}" color="{BLUE}" penwidth=2];
  B [label="Draw minimal sample\\ns points, uniformly at random"];
  C [label="Minimal solver\\nfit hypothesis θ" fillcolor="{GREEN_F}" color="{GREEN}" penwidth=2];
  D [label="Sample\\ndegenerate?" shape=diamond style=filled fillcolor="white" height=0.8];
  E [label="Compute residuals r_i\\nfor all n points"];
  F [label="Consensus set I\\n= points with r_i < t" fillcolor="{GREEN_F}" color="{GREEN}" penwidth=2];
  G [label="Score better than\\nbest so far?" shape=diamond style=filled fillcolor="white" height=0.9];
  H [label="Store θ, I as best"];
  I [label="Re-estimate w = |I| / n\\nshrink N = log(1−p) / log(1−w^s)"
     fillcolor="{RED_F}" color="{RED}" penwidth=2];
  J [label="Trial budget N\\nexhausted?" shape=diamond style=filled fillcolor="white" height=0.85];
  K [label="POLISH: refit on ALL inliers\\nwith the non-minimal solver"
     fillcolor="{PURPLE_F}" color="{PURPLE}" penwidth=2];
  L [label="Return model + inlier mask" fillcolor="{BLUE_F}" color="{BLUE}" penwidth=2];

  A -> B; B -> C; C -> D;
  D -> B [label="  yes" constraint=false];
  D -> E [label="  no"];
  E -> F; F -> G;
  G -> H [label="  yes"];
  H -> I; I -> J;
  G -> J [label="  no" constraint=false];
  J -> B [label="  no" constraint=false];
  J -> K [label="  yes"];
  K -> L;
}}
'''

PIPELINE = f'''
digraph pipeline {{
  rankdir=LR; bgcolor="transparent"; nodesep=0.28; ranksep=0.34;
  node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=10
        fillcolor="white" color="#3a3a3a" penwidth=1.2 margin="0.14,0.08"];
  edge [fontname="Helvetica" fontsize=9 color="#555555" arrowsize=0.7];

  A [label="Image pair"];
  B [label="Detect + describe\\nSIFT / SuperPoint / DISK"];
  C [label="Match descriptors\\nbrute force or FLANN"];
  D [label="Ratio test + mutual NN\\nraises w cheaply" fillcolor="{GREEN_F}" color="{GREEN}" penwidth=2];
  E [label="RANSAC\\nUSAC_MAGSAC" fillcolor="{BLUE_F}" color="{BLUE}" penwidth=2.6];
  F [label="Polish: refit\\non all inliers"];
  G [label="VALIDATE\\nsupport, conditioning,\\ngeometry" fillcolor="{RED_F}" color="{RED}" penwidth=2];
  H [label="H, F, E or pose"];
  I [label="Reject the pair"];

  A -> B -> C -> D -> E -> F -> G;
  G -> H [label="  pass"];
  G -> I [label="  fail"];
}}
'''

TAXONOMY = f'''
digraph taxonomy {{
  rankdir=TB; bgcolor="transparent"; nodesep=0.22; ranksep=0.45;
  node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=9.5
        fillcolor="white" color="#3a3a3a" penwidth=1.1 margin="0.12,0.07"];
  edge [color="#666666" arrowsize=0.6];

  R [label="RANSAC\\nFischler and Bolles, 1981"
     fillcolor="{BLUE_F}" color="{BLUE}" penwidth=2.6 fontsize=12];

  S [label="1 · SAMPLING\\nwhich minimal sets to try" fillcolor="#f2f4f6"];
  Q [label="2 · SCORING\\nwhat makes a model good" fillcolor="#f2f4f6"];
  V [label="3 · VERIFICATION\\nhow cheaply to test it" fillcolor="#f2f4f6"];
  L [label="4 · LOCAL OPTIMISATION\\nimprove a promising model" fillcolor="#f2f4f6"];
  D [label="5 · DEGENERACY\\nreject confident nonsense" fillcolor="#f2f4f6"];

  S1 [label="NAPSAC · P-NAPSAC\\nlocal neighbourhoods"];
  S2 [label="PROSAC\\nbest matches first"];
  S3 [label="NG-RANSAC · NeFSAC\\nlearned / filtered"];
  Q1 [label="MSAC\\ntruncated L2"];
  Q2 [label="MLESAC\\nlikelihood"];
  Q3 [label="MAGSAC · MAGSAC++\\nmarginalise over σ"];
  V1 [label="T(d,d) pre-test"];
  V2 [label="SPRT\\noptimal randomised"];
  V3 [label="Preemptive RANSAC\\nbounded time"];
  L1 [label="LO-RANSAC · LO+-RANSAC"];
  L2 [label="GC-RANSAC\\ngraph cut"];
  D1 [label="DEGENSAC\\ndominant plane"];
  D2 [label="QDEGSAC"];

  U [label="USAC · USACv20 · VSAC\\nunified frameworks combining\\nthe best of each column"
     fillcolor="{GREEN_F}" color="{GREEN}" penwidth=2.6 fontsize=11];

  R -> S; R -> Q; R -> V; R -> L; R -> D;
  S -> S1; S -> S2; S -> S3;
  Q -> Q1; Q -> Q2; Q -> Q3;
  V -> V1; V -> V2; V -> V3;
  L -> L1; L -> L2;
  D -> D1; D -> D2;
  S1 -> U [color="{GREEN}"]; Q3 -> U [color="{GREEN}"]; V2 -> U [color="{GREEN}"];
  L2 -> U [color="{GREEN}"]; D1 -> U [color="{GREEN}"];
}}
'''


def render(dot_src, name):
    out = HERE / f"dia_{name}.svg"
    # explicit UTF-8: the labels contain θ, σ, − and ·, which the default
    # Windows code page cannot encode
    r = subprocess.run(["dot", "-Tsvg"], input=dot_src, capture_output=True,
                       text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    svg = r.stdout[r.stdout.index("<svg"):]          # drop the XML/DOCTYPE preamble
    out.write_text(svg, encoding="utf-8")
    return out, len(svg)


if __name__ == "__main__":
    for src, name in [(LOOP, "loop"), (PIPELINE, "pipeline"), (TAXONOMY, "taxonomy")]:
        p, n = render(src, name)
        print(f"{p.name:22} {n:>7} bytes")
