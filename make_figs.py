import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9.5,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.5,
    "axes.edgecolor": "#3a3a3a",
    "axes.linewidth": 0.9,
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.6,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

INLIER = "#1f6fb2"
OUTLIER = "#cc3311"
TRUTH = "#111111"
RANSACC = "#0b8a3d"
OLSC = "#cc3311"
ACCENT = "#8a5fb0"

# ------------------------------------------------------------------ model
def fit_line(pts):
    pts = np.asarray(pts, float)
    mu = pts.mean(axis=0)
    _, s, vt = np.linalg.svd(pts - mu)
    if s[0] < 1e-12:
        return None
    n = vt[-1]
    return n, -n @ mu


def line_res(model, pts):
    n, c = model
    return np.abs(np.asarray(pts, float) @ n + c)


def ransac_trace(data, min_samples, thr, max_trials, seed, conf=0.99):
    """Returns best model, inlier mask, and per-trial (best_count, N_needed) trace."""
    rng = np.random.default_rng(seed)
    n = len(data)
    best = (None, np.zeros(n, bool), np.inf)
    trace = []
    N_needed = max_trials
    t = 0
    while t < min(N_needed, max_trials):
        t += 1
        idx = rng.choice(n, min_samples, replace=False)
        m = fit_line(data[idx])
        if m is not None:
            e = line_res(m, data)
            inl = e < thr
            k = int(inl.sum())
            if k >= min_samples:
                sc = float(e[inl].sum())
                if k > best[1].sum() or (k == best[1].sum() and sc < best[2]):
                    best = (m, inl, sc)
                    w = k / n
                    N_needed = math.ceil(
                        math.log(1 - conf) / math.log(max(1e-12, 1 - w ** min_samples))
                    )
        trace.append((int(best[1].sum()), min(N_needed, max_trials)))
    m, inl, _ = best
    if inl.sum() >= min_samples:
        m = fit_line(data[inl])
    return m, inl, np.array(trace)


# ------------------------------------------------------------------ data
rng = np.random.default_rng(0)
M_TRUE, B_TRUE, SIGMA = 0.6, -4.0, 0.4
NI, NO = 120, 80
x = rng.uniform(-20, 20, NI)
y = M_TRUE * x + B_TRUE + rng.normal(0, SIGMA, NI)
data = np.vstack([np.column_stack([x, y]),
                  np.column_stack([rng.uniform(-20, 20, NO),
                                   rng.uniform(-25, 25, NO)])])
truth = np.r_[np.ones(NI, bool), np.zeros(NO, bool)]

model, mask, trace = ransac_trace(data, 2, 3 * SIGMA, 2000, seed=7)
nrm, c = model
r_slope, r_int = -nrm[0] / nrm[1], -c / nrm[1]
A = np.column_stack([data[:, 0], np.ones(len(data))])
o_slope, o_int = np.linalg.lstsq(A, data[:, 1], rcond=None)[0]

fig, axes = plt.subplots(2, 2, figsize=(11.6, 8.4))
fig.suptitle("RANSAC: what it does, how long it takes, and how to tune it",
             fontsize=14, fontweight="bold", y=0.975)

# ---------------- panel A: the core idea
ax = axes[0, 0]
ax.scatter(data[~mask, 0], data[~mask, 1], s=16, c=OUTLIER, marker="x",
           linewidths=1.1, label=f"rejected as outlier (n={int((~mask).sum())})")
ax.scatter(data[mask, 0], data[mask, 1], s=15, facecolors="none",
           edgecolors=INLIER, linewidths=0.9,
           label=f"consensus set (n={int(mask.sum())})")
xx = np.array([-21, 21])
ax.plot(xx, r_slope * xx + r_int, color=RANSACC, lw=3.0,
        label=f"RANSAC  (slope {r_slope:.3f})")
ax.plot(xx, o_slope * xx + o_int, color=OLSC, lw=2.4,
        label=f"least squares, all data  (slope {o_slope:.3f})")
ax.plot(xx, M_TRUE * xx + B_TRUE, color=TRUTH, lw=1.6, ls=(0, (6, 4)),
        label=f"ground truth  (slope {M_TRUE:.3f})", zorder=5)
ax.set_title("A · 40 % of the data are outliers")
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.set_xlim(-21, 21); ax.set_ylim(-26, 26)
ax.legend(loc="upper left", fontsize=7.8)

# ---------------- panel B: iteration count
ax = axes[0, 1]
w = np.linspace(0.08, 0.98, 400)
for s, col, lbl in [(2, INLIER, "s=2  line"),
                    (3, RANSACC, "s=3  plane / P3P"),
                    (4, ACCENT, "s=4  homography"),
                    (5, "#e08214", "s=5  essential matrix"),
                    (7, OUTLIER, "s=7  fundamental matrix")]:
    N = np.log(1 - 0.99) / np.log(1 - w ** s)
    ax.plot(w, N, color=col, lw=2.0, label=lbl)
ax.set_yscale("log")
ax.set_title("B · Trials needed for 99 % confidence")
ax.set_xlabel("inlier ratio  w")
ax.set_ylabel(r"$N=\log(1-p)\,/\,\log(1-w^{s})$")
ax.set_xlim(0.08, 0.98); ax.set_ylim(1, 3e6)
ax.axhline(1e4, color="#888", lw=0.8, ls=":")
ax.text(0.62, 1.35e4, "10 000 trials", fontsize=7.5, color="#666")
ax.legend(loc="upper right")

# ---------------- panel C: threshold sweep
ax = axes[1, 0]
mults = np.array([0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 7, 10, 15, 20])
prec, rec, serr = [], [], []
for mlt in mults:
    p_, r_, e_ = [], [], []
    for seed in range(40):
        rr = np.random.default_rng(100 + seed)
        xi = rr.uniform(-20, 20, NI)
        yi = M_TRUE * xi + B_TRUE + rr.normal(0, SIGMA, NI)
        d = np.vstack([np.column_stack([xi, yi]),
                       np.column_stack([rr.uniform(-20, 20, NO),
                                        rr.uniform(-25, 25, NO)])])
        m_, k_, _ = ransac_trace(d, 2, mlt * SIGMA, 300, seed=seed)
        nn, cc = m_
        p_.append((k_ & truth).sum() / max(1, k_.sum()))
        r_.append((k_ & truth).sum() / truth.sum())
        e_.append(abs(-nn[0] / nn[1] - M_TRUE))
    prec.append(np.mean(p_)); rec.append(np.mean(r_)); serr.append(np.mean(e_))

ax.plot(mults, prec, "o-", color=INLIER, ms=4, lw=1.8, label="precision of inlier set")
ax.plot(mults, rec, "s-", color=RANSACC, ms=4, lw=1.8, label="recall of inlier set")
ax.set_xscale("log")
ax.set_xticks([0.5, 1, 2, 3, 5, 10, 20])
ax.set_xticklabels(["0.5", "1", "2", "3", "5", "10", "20"])
ax.set_xlabel(r"threshold  $t$  (in units of the true noise $\sigma$)")
ax.set_ylabel("precision / recall")
ax.set_ylim(0.3, 1.04)
ax.axvspan(1.96, 3.0, color=RANSACC, alpha=0.10, lw=0)
ax.text(2.42, 0.66, "useful\nrange", ha="center", fontsize=8.5, color="#0b6b30")
ax2 = ax.twinx()
ax2.plot(mults, serr, "^--", color=ACCENT, ms=4, lw=1.6)
ax2.set_ylabel("mean |slope error|", color=ACCENT)
ax2.tick_params(axis="y", colors=ACCENT)
ax2.set_yscale("log"); ax2.grid(False)
ax.set_title("C · Threshold is the one parameter that really matters")
h, l = ax.get_legend_handles_labels()
h.append(Line2D([], [], color=ACCENT, ls="--", marker="^", ms=4))
l.append("slope error (right axis)")
ax.legend(h, l, loc="lower left", fontsize=8)

# ---------------- panel D: adaptive termination
ax = axes[1, 1]
t = np.arange(1, len(trace) + 1)
ax.step(t, trace[:, 0], where="post", color=INLIER, lw=2.0,
        label="size of best consensus set so far")
ax.set_xlabel("trial index  k")
ax.set_ylabel("inliers found", color=INLIER)
ax.tick_params(axis="y", colors=INLIER)
ax.set_xlim(0.7, len(trace) + 0.6)
ax.set_ylim(0, 140)
axb = ax.twinx()
axb.step(t, trace[:, 1], where="post", color=OUTLIER, lw=2.0, ls="--",
         label="$N$ re-estimated from current $w$")
axb.set_yscale("log")
axb.set_ylabel("remaining trials budget $N$", color=OUTLIER)
axb.tick_params(axis="y", colors=OUTLIER)
axb.grid(False)
axb.axhline(len(trace), color="#666", lw=0.9, ls=":")
axb.text(len(trace) * 0.30, len(trace) * 1.6,
         f"stopped after {len(trace)} trials", fontsize=8, color="#444")
ax.set_title("D · Adaptive stopping: the budget collapses as $w$ is learned")
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = axb.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="center right", fontsize=8)

fig.tight_layout(rect=[0, 0, 1, 0.955])
fig.savefig("/home/claude/ransac_figures.png", dpi=170)
print("saved")
print("RANSAC slope", r_slope, "OLS slope", o_slope, "trials", len(trace),
      "inliers", int(mask.sum()))
