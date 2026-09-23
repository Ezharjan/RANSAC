"""
A compact, production-shaped RANSAC engine — the reference implementation
for the tutorial. Pure NumPy, no dependencies beyond it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np


# ======================================================================
#  The engine
# ======================================================================
@dataclass
class RansacResult:
    model: object
    inliers: np.ndarray                      # boolean mask, length n
    n_trials: int
    inlier_ratio: float
    residual_scale: float                    # robust sigma estimate
    converged: bool = field(default=True)   # confidence reached within cap


def ransac(
    data: np.ndarray,
    fit: Callable[[np.ndarray], object],
    residuals: Callable[[object, np.ndarray], np.ndarray],
    min_samples: int,
    threshold: float,
    *,
    max_trials: int = 10_000,
    confidence: float = 0.99,
    refit: Optional[Callable[[np.ndarray], object]] = None,
    score: str = "msac",
    is_sample_valid: Optional[Callable[[np.ndarray], bool]] = None,
    rng=None,
) -> RansacResult:
    """
    Robustly fit a model to `data` in the presence of outliers.

    Parameters
    ----------
    data          (n, ...) array. Row i is one datum.
    fit           fit(sample) -> model, or None if the sample is degenerate.
    residuals     residuals(model, data) -> (n,) array of non-negative errors.
    min_samples   s, the minimal sample size for `fit`.
    threshold     t, the inlier threshold, in the units of `residuals`.
    max_trials    hard cap; always keep one.
    confidence    p, the probability of drawing >=1 uncontaminated sample.
    refit         non-minimal solver used to polish on the full consensus set.
    score         "ransac" -> inlier count      (Fischler & Bolles 1981)
                  "msac"   -> truncated L2 cost (Torr & Zisserman 2000)
    is_sample_valid  optional cheap pre-check on the drawn sample.
    rng           seed or np.random.Generator, for reproducibility.
    """
    rng = np.random.default_rng(rng)
    data = np.asarray(data)
    n = len(data)
    if n < min_samples:
        raise ValueError(f"need >= {min_samples} data points, got {n}")
    if score not in ("ransac", "msac"):
        raise ValueError("score must be 'ransac' or 'msac'")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between 0 and 1")

    t2 = threshold * threshold
    best_model = None
    best_inliers = np.zeros(n, dtype=bool)
    best_score = -np.inf
    trials = 0
    budget = math.inf                        # adaptive N; shrinks as w is learned

    while trials < min(budget, max_trials):
        trials += 1

        # ---------------- 1. HYPOTHESISE --------------------------------
        idx = rng.choice(n, size=min_samples, replace=False)
        sample = data[idx]
        if is_sample_valid is not None and not is_sample_valid(sample):
            continue
        model = fit(sample)
        if model is None:                     # degenerate configuration
            continue

        # ---------------- 2. VERIFY -------------------------------------
        res = np.asarray(residuals(model, data), dtype=float)
        inliers = res < threshold
        n_in = int(inliers.sum())
        if n_in < min_samples:
            continue

        # ---------------- 3. SCORE --------------------------------------
        if score == "ransac":
            # inlier count, with total residual as tie-break
            current = n_in - 1e-9 * float(res[inliers].sum())
        else:
            # MSAC: truncated quadratic. Outliers contribute a constant t^2,
            # inliers contribute their squared residual. Lower cost = better,
            # so negate to keep "higher is better".
            cost = float(np.minimum(res * res, t2).sum())
            current = -cost

        if current > best_score:
            best_model, best_inliers, best_score = model, inliers, current

            # ---------- 4. ADAPTIVE TERMINATION -------------------------
            budget = min(budget, _trials_needed(n_in / n, min_samples,
                                                confidence))

    if best_model is None:
        return RansacResult(None, best_inliers, trials, 0.0, float("nan"),
                            converged=False)

    # -------------------- 5. POLISH -------------------------------------
    if refit is not None and best_inliers.sum() >= min_samples:
        polished = refit(data[best_inliers])
        if polished is not None:
            res = np.asarray(residuals(polished, data), dtype=float)
            new_inliers = res < threshold
            # accept the polish only if it does not lose support
            if new_inliers.sum() >= best_inliers.sum():
                best_model, best_inliers = polished, new_inliers

    # Robust noise scale. The residuals are unsigned distances of zero-mean
    # errors, so median(|r|) = 0.6745 sigma for a Gaussian with one degree of
    # freedom (codimension 1: lines, planes, circles). Taking the MAD of |r|
    # around its own median would under-estimate sigma by ~40 %.
    final_res = np.asarray(residuals(best_model, data), dtype=float)
    inlier_res = final_res[best_inliers]
    sigma = 1.4826 * float(np.median(inlier_res)) \
        if inlier_res.size else float("nan")

    return RansacResult(
        model=best_model,
        inliers=best_inliers,
        n_trials=trials,
        inlier_ratio=float(best_inliers.mean()),
        residual_scale=sigma,
        converged=budget <= max_trials,     # False: stopped by the hard cap
    )


def _trials_needed(w, s, confidence):
    """N = ceil(log(1-p) / log(1-w^s)), computed stably for tiny w^s."""
    q = w ** s
    if q >= 1.0:
        return 1
    if q <= 0.0:
        return math.inf
    # log1p keeps precision when q is tiny; plain log(1 - q) rounds to 0
    # (division by zero) once q drops below ~1e-16.
    denom = math.log1p(-q)
    if denom == 0.0:
        return math.inf
    return math.ceil(math.log(1.0 - confidence) / denom)


# ======================================================================
#  Model 1 — 2-D line, implicit form  n . x + c = 0,  |n| = 1
# ======================================================================
def fit_line(pts):
    """Total-least-squares line. Handles the minimal case (2 pts) and beyond."""
    pts = np.asarray(pts, float)
    centroid = pts.mean(axis=0)
    _, sv, vt = np.linalg.svd(pts - centroid)
    if sv[0] < 1e-12:                         # all points coincide
        return None
    normal = vt[-1]                           # least-variance direction
    return normal, float(-normal @ centroid)


def line_residuals(model, pts):
    normal, c = model
    return np.abs(np.asarray(pts, float) @ normal + c)


def line_to_slope_intercept(model):
    (a, b), c = model
    if abs(b) < 1e-12:
        return float("inf"), float("nan")     # vertical line
    return -a / b, -c / b


# ======================================================================
#  Model 2 — 2-D circle  (cx, cy, r),  minimal sample = 3
# ======================================================================
def fit_circle(pts):
    """Algebraic (Kasa) circle fit: linear least squares on x^2+y^2 = ..."""
    pts = np.asarray(pts, float)
    x, y = pts[:, 0], pts[:, 1]
    A = np.column_stack([x, y, np.ones(len(pts))])
    sv = np.linalg.svd(A, compute_uv=False)
    if len(pts) < 3 or sv[-1] <= 1e-9 * sv[0]:   # collinear/coincident sample
        return None
    b = x * x + y * y
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = sol[0] / 2.0, sol[1] / 2.0
    disc = sol[2] + cx * cx + cy * cy
    if disc <= 0:
        return None
    return cx, cy, math.sqrt(disc)


def circle_residuals(model, pts):
    cx, cy, r = model
    pts = np.asarray(pts, float)
    return np.abs(np.hypot(pts[:, 0] - cx, pts[:, 1] - cy) - r)


# ======================================================================
#  Model 3 — 3-D plane  n . x + d = 0,  minimal sample = 3
# ======================================================================
def fit_plane(pts):
    pts = np.asarray(pts, float)
    centroid = pts.mean(axis=0)
    _, sv, vt = np.linalg.svd(pts - centroid)
    # need genuine 2-D spread, else the sample is collinear/coincident
    if sv[1] < 1e-9 * max(sv[0], 1e-12):
        return None
    normal = vt[-1]
    return normal, float(-normal @ centroid)


def plane_residuals(model, pts):
    normal, d = model
    return np.abs(np.asarray(pts, float) @ normal + d)


# ======================================================================
#  Demonstration
# ======================================================================
if __name__ == "__main__":
    rng = np.random.default_rng(0)

    # ---------- line, 40 % outliers ------------------------------------
    M, B, SIG, NI, NO = 0.6, -4.0, 0.4, 120, 80
    x = rng.uniform(-20, 20, NI)
    pts = np.vstack([
        np.column_stack([x, M * x + B + rng.normal(0, SIG, NI)]),
        np.column_stack([rng.uniform(-20, 20, NO), rng.uniform(-25, 25, NO)]),
    ])
    truth = np.r_[np.ones(NI, bool), np.zeros(NO, bool)]

    PAD = " " * 14                             # indent for continuation lines
    for mode in ("ransac", "msac"):
        r = ransac(pts, fit_line, line_residuals, 2, 3 * SIG,
                   refit=fit_line, score=mode, rng=7)
        sl, ic = line_to_slope_intercept(r.model)
        tp = int((r.inliers & truth).sum())
        print(f"LINE [{mode:6s}] slope={sl:+.4f} (true {M:+.4f})  "
              f"intercept={ic:+.4f} (true {B:+.4f})  trials={r.n_trials:3d}")
        print(f"{PAD}inliers={int(r.inliers.sum()):3d}  "
              f"precision={tp / max(1, r.inliers.sum()):.3f}  "
              f"recall={tp / truth.sum():.3f}  sigma_hat={r.residual_scale:.3f}")

    A = np.column_stack([pts[:, 0], np.ones(len(pts))])
    ols = np.linalg.lstsq(A, pts[:, 1], rcond=None)[0]
    print(f"LINE [OLS   ] slope={ols[0]:+.4f} (true {M:+.4f})  "
          f"intercept={ols[1]:+.4f} (true {B:+.4f})")
    print(f"{PAD}<-- destroyed by outliers")

    # ---------- circle, 50 % outliers ---------------------------------
    CX, CY, R = 3.0, -2.0, 5.0
    th = rng.uniform(0, 2 * np.pi, 100)
    cpts = np.vstack([
        np.column_stack([CX + R * np.cos(th) + rng.normal(0, 0.1, 100),
                         CY + R * np.sin(th) + rng.normal(0, 0.1, 100)]),
        rng.uniform(-12, 12, (100, 2)),
    ])
    rc = ransac(cpts, fit_circle, circle_residuals, 3, 0.3,
                refit=fit_circle, rng=1)
    print()
    print(f"CIRCLE        centre=({rc.model[0]:+.3f},{rc.model[1]:+.3f}) "
          f"r={rc.model[2]:.3f}  (true ({CX:+.1f},{CY:+.1f}) r={R:.1f})")
    print(f"{PAD}trials={rc.n_trials}   inliers={int(rc.inliers.sum())}")

    # ---------- plane, 60 % outliers ----------------------------------
    n_true = np.array([0.2, -0.3, 1.0]); n_true /= np.linalg.norm(n_true)
    d_true = -1.5
    uv = rng.uniform(-5, 5, (120, 2))
    basis = np.linalg.svd(n_true.reshape(1, -1))[2][1:]
    on_plane = uv @ basis - d_true * n_true + rng.normal(0, 0.05, (120, 3))
    ppts = np.vstack([on_plane, rng.uniform(-8, 8, (180, 3))])
    rp = ransac(ppts, fit_plane, plane_residuals, 3, 0.15,
                refit=fit_plane, rng=2)
    nn, dd = rp.model
    if nn @ n_true < 0:
        nn, dd = -nn, -dd                     # fix sign ambiguity
    vec = lambda v: "[" + " ".join(f"{c:.3f}" for c in v) + "]"
    print()
    print(f"PLANE         normal={vec(nn)} d={dd:+.3f}  "
          f"(true {vec(n_true)} d={d_true:+.3f})")
    print(f"{PAD}angle_err={math.degrees(math.acos(min(1, abs(nn @ n_true)))):.3f} deg"
          f"   trials={rp.n_trials}   inliers={int(rp.inliers.sum())}")
