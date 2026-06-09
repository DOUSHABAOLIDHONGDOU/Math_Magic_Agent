"""
Q1 Scheme B v2 – Spline Regression (GAM-style) for Y-chromosome concentration
Model: Y_ij = f1(gestation) + f2(bmi) + f3(gestation,bmi) + gamma*quality + eps

Fixes vs v1:
  1. MPLCONFIGDIR set BEFORE importing matplotlib
  2. Leak-free GroupKFold CV: transformers fitted inside each outer fold
  3. Inner GroupKFold alpha selection within each outer training set
  4. Fixed-basis group bootstrap for CI (subjects sampled w/ replacement;
     final model's transformers kept fixed; only Ridge refitted per bootstrap)
  5. Gestational week upper limit: primary analysis <=25 weeks (per problem statement);
     <=26 sensitivity comparison table also output
  6. Sanity checks on predictions and CI bands; warnings logged
  7. All outputs regenerated

Run from project root:
    python3 05_code/Q1/q1_scheme_B.py
"""

# ── Fix 1: MPLCONFIGDIR before matplotlib import ──────────────────────────────
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MPLCACHE  = os.path.join(_REPO_ROOT, '.cache', 'matplotlib')
os.makedirs(_MPLCACHE, exist_ok=True)
os.environ['MPLCONFIGDIR'] = _MPLCACHE

import re
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
from sklearn.preprocessing import SplineTransformer, StandardScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error
from scipy import stats

warnings.filterwarnings('ignore')
SEED = 42
np.random.seed(SEED)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = _REPO_ROOT
DATA_PATH = os.path.join(ROOT, '01_problem', 'source',
                         'CUMCM2025Problems', 'C题', '附件.xlsx')
OUT_TABLES = os.path.join(ROOT, '06_results', 'Q1', 'tables')
OUT_FIGS   = os.path.join(ROOT, '06_results', 'Q1', 'figures')
OUT_LOGS   = os.path.join(ROOT, '06_results', 'Q1', 'logs')
for d in [OUT_TABLES, OUT_FIGS, OUT_LOGS]:
    os.makedirs(d, exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
ALPHAS    = np.logspace(-2, 3, 20)   # alpha search grid
N_OUTER   = 5                         # outer GroupKFold folds
N_INNER   = 3                         # inner GroupKFold folds for alpha selection
N_BOOT    = 200                       # bootstrap iterations
N_INTER   = 3                         # spline basis cols used for interaction term
N_KNOTS   = 5                         # knots per spline
DEGREES   = [3, 4, 5, 6]             # spline degrees to evaluate
QC_COLS   = ['GC含量',
             '在参考基因组上比对的比例',
             '重复读段的比例',
             '被过滤掉读段数的比例']

# ── Sanity log ────────────────────────────────────────────────────────────────
SANITY_LOG = []


def _sanity(name, arr, lo=-0.001, hi=0.50):
    """Warn if any value falls outside plausible Y-concentration range."""
    arr = np.asarray(arr, dtype=float)
    n_lo = int(np.sum(arr < lo))
    n_hi = int(np.sum(arr > hi))
    if n_lo > 0:
        msg = f"[SANITY WARN] {name}: {n_lo} values < {lo:.3f} (min={arr.min():.4f})"
        SANITY_LOG.append(msg)
        print(f"  *** {msg}")
    if n_hi > 0:
        msg = f"[SANITY WARN] {name}: {n_hi} values > {hi:.3f} (max={arr.max():.4f})"
        SANITY_LOG.append(msg)
        print(f"  *** {msg}")
    return arr


def _clip_ci(lo_arr, hi_arr, name):
    """Clip bootstrap CI to [0, 0.50]; log if clamping was needed."""
    n_clipped = int(np.sum(lo_arr < 0) + np.sum(hi_arr > 0.50))
    lo_c = np.clip(lo_arr, 0.0, 0.50)
    hi_c = np.clip(hi_arr, 0.0, 0.50)
    if n_clipped > 0:
        msg = (f"[SANITY WARN] {name}: {n_clipped} CI bounds clamped to [0, 0.50]; "
               f"raw lo_min={lo_arr.min():.4f}, hi_max={hi_arr.max():.4f}")
        SANITY_LOG.append(msg)
        print(f"  *** {msg}")
    return lo_c, hi_c


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_gestation_week(s):
    """'12w+3' → 12.429, '13w' → 13.0"""
    if pd.isna(s):
        return np.nan
    s = str(s).strip()
    m = re.match(r'^(\d+)w\+(\d+)$', s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 7.0
    m = re.match(r'^(\d+)w$', s)
    if m:
        return float(m.group(1))
    try:
        return float(s)
    except ValueError:
        return np.nan


def calc_rmse(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def build_features(g_col, b_col, qc_mat, sg, sb):
    """Transform gestation + BMI splines + interaction + QC into feature matrix."""
    Xg = sg.transform(g_col)
    Xb = sb.transform(b_col)
    Xi = np.einsum('ij,ik->ijk',
                   Xg[:, :N_INTER],
                   Xb[:, :N_INTER]).reshape(len(g_col), -1)
    return np.hstack([Xg, Xb, Xi, qc_mat])


def select_alpha_inner(X_sc, y_, groups_, alphas, inner_cv):
    """Select ridge alpha via inner GroupKFold on already-scaled train features."""
    best_a, best_err = alphas[0], np.inf
    for a in alphas:
        errs = []
        for itr, ite in inner_cv.split(X_sc, y_, groups=groups_):
            m = Ridge(alpha=a).fit(X_sc[itr], y_[itr])
            errs.append(calc_rmse(y_[ite], m.predict(X_sc[ite])))
        mean_err = float(np.mean(errs))
        if mean_err < best_err:
            best_err = mean_err
            best_a   = a
    return best_a


# ── 1. Load & clean ───────────────────────────────────────────────────────────
print("Loading data …")
df_raw = pd.read_excel(DATA_PATH, sheet_name='男胎检测数据')
df_raw.columns = df_raw.columns.str.strip()
df_raw['孕周'] = df_raw['检测孕周'].apply(parse_gestation_week)

required = ['孕周', 'Y染色体浓度', '孕妇BMI', '孕妇代码']
df_base  = df_raw.dropna(subset=required).copy()
df_base  = df_base[(df_base['孕周'] >= 10) & (df_base['Y染色体浓度'] > 0)]

# Fix 5: primary uses <= 25 weeks (problem statement boundary)
df_25 = df_base[df_base['孕周'] <= 25].reset_index(drop=True)
df_26 = df_base[df_base['孕周'] <= 26].reset_index(drop=True)
print(f"  Cleaned <=25w: {len(df_25)} rows, {df_25['孕妇代码'].nunique()} subjects")
print(f"  Cleaned <=26w: {len(df_26)} rows, {df_26['孕妇代码'].nunique()} subjects")

# Primary analysis dataset
df = df_25.copy()
TARGET = 'Y染色体浓度'

y         = df[TARGET].values
groups    = df['孕妇代码'].values
gestation = df['孕周'].values.reshape(-1, 1)
bmi       = df['孕妇BMI'].values.reshape(-1, 1)
qc        = df[QC_COLS].values
N         = len(df)

outer_gkf = GroupKFold(n_splits=N_OUTER)
inner_gkf = GroupKFold(n_splits=N_INNER)


# ── 2. Fix 2 & 3: Leak-free outer CV with inner alpha selection ───────────────
print(f"\nLeak-free {N_OUTER}-fold GroupKFold CV (inner {N_INNER}-fold alpha selection) …")

cv_records = []  # one record per (degree, fold)

for deg in DEGREES:
    for fold_i, (tr_idx, te_idx) in enumerate(outer_gkf.split(gestation, y, groups=groups)):
        # ─ Train subset ─
        g_tr, b_tr  = gestation[tr_idx], bmi[tr_idx]
        qc_tr       = qc[tr_idx]
        y_tr        = y[tr_idx]
        grp_tr      = groups[tr_idx]

        # ─ Test subset ─
        g_te, b_te  = gestation[te_idx], bmi[te_idx]
        qc_te       = qc[te_idx]
        y_te        = y[te_idx]

        # Fit splines on train only
        sg = SplineTransformer(degree=deg, n_knots=N_KNOTS, include_bias=False).fit(g_tr)
        sb = SplineTransformer(degree=deg, n_knots=N_KNOTS, include_bias=False).fit(b_tr)

        X_tr_raw = build_features(g_tr, b_tr, qc_tr, sg, sb)
        X_te_raw = build_features(g_te, b_te, qc_te, sg, sb)

        sc = StandardScaler().fit(X_tr_raw)
        X_tr_sc = sc.transform(X_tr_raw)
        X_te_sc = sc.transform(X_te_raw)

        # Inner GroupKFold alpha selection (Fix 3)
        best_a = select_alpha_inner(X_tr_sc, y_tr, grp_tr, ALPHAS, inner_gkf)

        m = Ridge(alpha=best_a).fit(X_tr_sc, y_tr)
        p = m.predict(X_te_sc)

        ss_res = float(np.sum((y_te - p) ** 2))
        ss_tot = float(np.sum((y_te - y_te.mean()) ** 2))
        fold_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        # Linear baseline (same outer fold, fix scaler leakage)
        X_lin_tr = np.hstack([g_tr, b_tr, qc_tr])
        X_lin_te = np.hstack([g_te, b_te, qc_te])
        sc_lin   = StandardScaler().fit(X_lin_tr)
        X_lin_tr_sc = sc_lin.transform(X_lin_tr)
        X_lin_te_sc = sc_lin.transform(X_lin_te)

        best_a_lin = select_alpha_inner(X_lin_tr_sc, y_tr, grp_tr, ALPHAS, inner_gkf)
        m_lin      = Ridge(alpha=best_a_lin).fit(X_lin_tr_sc, y_tr)
        p_lin      = m_lin.predict(X_lin_te_sc)
        ss_res_lin = float(np.sum((y_te - p_lin) ** 2))
        fold_r2_lin = 1.0 - ss_res_lin / ss_tot if ss_tot > 0 else 0.0

        cv_records.append({
            'degree':        deg,
            'fold':          fold_i,
            'spline_rmse':   calc_rmse(y_te, p),
            'spline_r2':     fold_r2,
            'spline_alpha':  best_a,
            'linear_rmse':   calc_rmse(y_te, p_lin),
            'linear_r2':     fold_r2_lin,
            'linear_alpha':  best_a_lin,
        })

cv_df = pd.DataFrame(cv_records)

# Aggregate per degree
agg = (cv_df.groupby('degree')
       .agg(
           spline_cv_rmse_mean=('spline_rmse', 'mean'),
           spline_cv_rmse_std =('spline_rmse', 'std'),
           spline_cv_r2_mean  =('spline_r2',   'mean'),
           linear_cv_rmse_mean=('linear_rmse', 'mean'),
           linear_cv_r2_mean  =('linear_r2',   'mean'),
       )
       .reset_index())

for _, row in agg.iterrows():
    print(f"  deg={int(row.degree)}  "
          f"Spline CV-RMSE={row.spline_cv_rmse_mean:.5f}±{row.spline_cv_rmse_std:.5f}  "
          f"R²={row.spline_cv_r2_mean:.4f}  |  "
          f"Linear RMSE={row.linear_cv_rmse_mean:.5f}  R²={row.linear_cv_r2_mean:.4f}")

best_deg = int(agg.loc[agg['spline_cv_rmse_mean'].idxmin(), 'degree'])
print(f"  → Best spline degree: {best_deg}")

# Best linear baseline metrics (same across all degrees)
lin_cv_rmse = float(agg.loc[agg['degree'] == best_deg, 'linear_cv_rmse_mean'])
lin_cv_r2   = float(agg.loc[agg['degree'] == best_deg, 'linear_cv_r2_mean'])
sp_cv_rmse  = float(agg.loc[agg['degree'] == best_deg, 'spline_cv_rmse_mean'])
sp_cv_r2    = float(agg.loc[agg['degree'] == best_deg, 'spline_cv_r2_mean'])


# ── 3. Final model on full data ───────────────────────────────────────────────
print(f"\nFitting final model (degree={best_deg}) on full data …")

# Fit transformers on all data
spl_g_final = SplineTransformer(degree=best_deg, n_knots=N_KNOTS, include_bias=False)
spl_b_final = SplineTransformer(degree=best_deg, n_knots=N_KNOTS, include_bias=False)
spl_g_final.fit(gestation)
spl_b_final.fit(bmi)

X_full     = build_features(gestation, bmi, qc, spl_g_final, spl_b_final)
scaler_fin = StandardScaler().fit(X_full)
X_full_sc  = scaler_fin.transform(X_full)

# Select alpha via inner GroupKFold on full data
best_alpha_full = select_alpha_inner(X_full_sc, y, groups, ALPHAS, inner_gkf)
print(f"  Full-data alpha: {best_alpha_full:.4f}")

model_final = Ridge(alpha=best_alpha_full).fit(X_full_sc, y)
y_pred      = model_final.predict(X_full_sc)

_sanity("final_train_pred", y_pred)
train_rmse = calc_rmse(y, y_pred)
ss_res_full = float(np.sum((y - y_pred) ** 2))
ss_tot_full = float(np.sum((y - y.mean()) ** 2))
train_r2    = 1.0 - ss_res_full / ss_tot_full
print(f"  Train RMSE={train_rmse:.5f}  R²={train_r2:.4f}")


# ── 4. Partial effects (marginal averaging) ───────────────────────────────────
print("\nComputing partial effects …")
g_grid  = np.linspace(float(gestation.min()), float(gestation.max()), 100)
b_grid  = np.linspace(float(bmi.min()),       float(bmi.max()),       100)
bmi_med = float(np.median(bmi))
g_med   = float(np.median(gestation))
qc_med  = np.median(qc, axis=0)


def _partial_g(g_arr, b_fix, qc_fix, sg, sb, sc, m):
    g_ = np.asarray(g_arr).reshape(-1, 1)
    b_ = np.full_like(g_, b_fix)
    qc_ = np.tile(qc_fix, (len(g_), 1))
    X_ = build_features(g_, b_, qc_, sg, sb)
    return m.predict(sc.transform(X_))


def _partial_b(b_arr, g_fix, qc_fix, sg, sb, sc, m):
    b_ = np.asarray(b_arr).reshape(-1, 1)
    g_ = np.full_like(b_, g_fix)
    qc_ = np.tile(qc_fix, (len(b_), 1))
    X_ = build_features(g_, b_, qc_, sg, sb)
    return m.predict(sc.transform(X_))


partial_g_pred = _partial_g(g_grid, bmi_med, qc_med,
                             spl_g_final, spl_b_final, scaler_fin, model_final)
partial_b_pred = _partial_b(b_grid, g_med, qc_med,
                             spl_g_final, spl_b_final, scaler_fin, model_final)

_sanity("partial_gestation", partial_g_pred)
_sanity("partial_bmi",       partial_b_pred)


# ── 5. Fix 4: Fixed-basis group bootstrap CI ──────────────────────────────────
print(f"\nFixed-basis group bootstrap (N={N_BOOT}, sampling by 孕妇代码) …")

subject_codes = np.unique(groups)

# Build subject-to-index lookup once
subj_idx_map = {}
for subj in subject_codes:
    subj_idx_map[subj] = np.where(groups == subj)[0]

boot_g_mat = np.zeros((N_BOOT, len(g_grid)))
boot_b_mat = np.zeros((N_BOOT, len(b_grid)))

for i in range(N_BOOT):
    rng = np.random.RandomState(SEED + i)
    # Sample subjects with replacement (group bootstrap)
    boot_subjs = rng.choice(subject_codes, size=len(subject_codes), replace=True)

    boot_idx = np.concatenate([subj_idx_map[s] for s in boot_subjs])
    y_b  = y[boot_idx]
    X_b  = X_full_sc[boot_idx]   # use final model's fixed transformers

    m_b = Ridge(alpha=best_alpha_full).fit(X_b, y_b)

    boot_g_mat[i] = _partial_g(g_grid, bmi_med, qc_med,
                                spl_g_final, spl_b_final, scaler_fin, m_b)
    boot_b_mat[i] = _partial_b(b_grid, g_med, qc_med,
                                spl_g_final, spl_b_final, scaler_fin, m_b)

ci_g_lo_raw, ci_g_hi_raw = np.percentile(boot_g_mat, [2.5, 97.5], axis=0)
ci_b_lo_raw, ci_b_hi_raw = np.percentile(boot_b_mat, [2.5, 97.5], axis=0)

# Sanity check + clip CI
ci_g_lo, ci_g_hi = _clip_ci(ci_g_lo_raw, ci_g_hi_raw, "CI_gestation")
ci_b_lo, ci_b_hi = _clip_ci(ci_b_lo_raw, ci_b_hi_raw, "CI_bmi")

print(f"  Gestation CI range: [{ci_g_lo.min():.4f}, {ci_g_hi.max():.4f}]")
print(f"  BMI       CI range: [{ci_b_lo.min():.4f}, {ci_b_hi.max():.4f}]")


# ── 6. 2D heatmap ─────────────────────────────────────────────────────────────
print("\nComputing 2D heatmap …")
g_hm = np.linspace(float(gestation.min()), float(gestation.max()), 50)
b_hm = np.linspace(float(bmi.min()),       float(bmi.max()),       50)
GG, BB = np.meshgrid(g_hm, b_hm)
g_flat = GG.ravel().reshape(-1, 1)
b_flat = BB.ravel().reshape(-1, 1)
qc_hm  = np.tile(qc_med, (len(g_flat), 1))
X_hm   = build_features(g_flat, b_flat, qc_hm, spl_g_final, spl_b_final)
Z_raw  = model_final.predict(scaler_fin.transform(X_hm))
_sanity("heatmap_pred", Z_raw)
Z_hm   = np.clip(Z_raw, 0.0, None).reshape(50, 50)


# ── 7. Fix 5: Sensitivity analysis <=25 vs <=26 weeks ─────────────────────────
print(f"\nSensitivity: comparing <=25w vs <=26w for degree={best_deg} …")

sens_records = []
for label, df_s in [('<=25w', df_25), ('<=26w', df_26)]:
    y_s  = df_s[TARGET].values
    g_s  = df_s['孕周'].values.reshape(-1, 1)
    b_s  = df_s['孕妇BMI'].values.reshape(-1, 1)
    qc_s = df_s[QC_COLS].values
    grp_s = df_s['孕妇代码'].values

    fold_rmse_s, fold_r2_s = [], []
    for tr_i, te_i in GroupKFold(n_splits=N_OUTER).split(g_s, y_s, groups=grp_s):
        g_tr, b_tr = g_s[tr_i], b_s[tr_i]
        sg = SplineTransformer(degree=best_deg, n_knots=N_KNOTS, include_bias=False).fit(g_tr)
        sb = SplineTransformer(degree=best_deg, n_knots=N_KNOTS, include_bias=False).fit(b_tr)
        X_tr = build_features(g_tr, b_s[tr_i], qc_s[tr_i], sg, sb)
        sc_s = StandardScaler().fit(X_tr)
        X_tr_sc = sc_s.transform(X_tr)
        X_te_sc = sc_s.transform(build_features(g_s[te_i], b_s[te_i], qc_s[te_i], sg, sb))
        a_s = select_alpha_inner(X_tr_sc, y_s[tr_i], grp_s[tr_i], ALPHAS, inner_gkf)
        p_s = Ridge(alpha=a_s).fit(X_tr_sc, y_s[tr_i]).predict(X_te_sc)
        fold_rmse_s.append(calc_rmse(y_s[te_i], p_s))
        ss_r = float(np.sum((y_s[te_i] - p_s) ** 2))
        ss_t = float(np.sum((y_s[te_i] - y_s[te_i].mean()) ** 2))
        fold_r2_s.append(1 - ss_r / ss_t if ss_t > 0 else 0.0)

    sens_records.append({
        'dataset':   label,
        'n_rows':    len(df_s),
        'n_subjects': df_s['孕妇代码'].nunique(),
        'gestation_max': df_s['孕周'].max(),
        'cv_rmse':   float(np.mean(fold_rmse_s)),
        'cv_r2':     float(np.mean(fold_r2_s)),
    })
    print(f"  {label}: CV-RMSE={np.mean(fold_rmse_s):.5f}  CV-R²={np.mean(fold_r2_s):.4f}")

sens_df = pd.DataFrame(sens_records)


# ── 8. Residual analysis ──────────────────────────────────────────────────────
residuals = y - y_pred
_, p_shapiro = stats.shapiro(residuals[:500])
stat_bp, p_bp = stats.pearsonr(y_pred, residuals)


# ── 9. Save tables ─────────────────────────────────────────────────────────────
print("\nSaving tables …")

# Main metrics
metrics_df = pd.DataFrame([{
    'model':             'Spline-Ridge-v2 (B)',
    'best_degree':       best_deg,
    'n_knots':           N_KNOTS,
    'alpha':             best_alpha_full,
    'train_rmse':        train_rmse,
    'train_r2':          train_r2,
    'cv_rmse_spline':    sp_cv_rmse,
    'cv_r2_spline':      sp_cv_r2,
    'cv_rmse_linear':    lin_cv_rmse,
    'cv_r2_linear':      lin_cv_r2,
    'delta_rmse':        lin_cv_rmse - sp_cv_rmse,
    'residual_shapiro_p': p_shapiro,
    'residual_pearson_r':  stat_bp,
    'residual_pearson_p':  p_bp,
    'n_samples':         N,
    'n_subjects':        len(subject_codes),
    'gestation_range':   f"{gestation.min():.1f}–{gestation.max():.1f}",
    'bmi_range':         f"{bmi.min():.1f}–{bmi.max():.1f}",
    'sanity_warnings':   len(SANITY_LOG),
}])
metrics_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_metrics.csv'), index=False)

# CV comparison (aggregated per degree)
agg_export = agg.copy()
agg_export.to_csv(os.path.join(OUT_TABLES, 'scheme_B_cv_comparison.csv'), index=False)

# Full fold-level CV records
cv_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_cv_folds.csv'), index=False)

# Sensitivity: degree 3–6 for best model
sensitivity_deg = agg[['degree', 'spline_cv_rmse_mean', 'spline_cv_rmse_std', 'spline_cv_r2_mean']].copy()
sensitivity_deg.columns = ['spline_degree', 'cv_rmse_mean', 'cv_rmse_std', 'cv_r2_mean']
sensitivity_deg.to_csv(os.path.join(OUT_TABLES, 'scheme_B_sensitivity_degree.csv'), index=False)

# Sensitivity: <=25 vs <=26 weeks
sens_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_sensitivity_gestation_cutoff.csv'), index=False)

# Partial effect data (with sanity-checked CI)
pd.DataFrame({
    'gestation_week':    g_grid,
    'predicted_Y_conc':  partial_g_pred,
    'ci_lo':             ci_g_lo,
    'ci_hi':             ci_g_hi,
    'ci_lo_raw':         ci_g_lo_raw,
    'ci_hi_raw':         ci_g_hi_raw,
}).to_csv(os.path.join(OUT_TABLES, 'scheme_B_partial_gestation.csv'), index=False)

pd.DataFrame({
    'bmi':               b_grid,
    'predicted_Y_conc':  partial_b_pred,
    'ci_lo':             ci_b_lo,
    'ci_hi':             ci_b_hi,
    'ci_lo_raw':         ci_b_lo_raw,
    'ci_hi_raw':         ci_b_hi_raw,
}).to_csv(os.path.join(OUT_TABLES, 'scheme_B_partial_bmi.csv'), index=False)

# 2D heatmap grid
pd.DataFrame({
    'gestation_week': GG.ravel(),
    'bmi':            BB.ravel(),
    'predicted_Y_conc': Z_hm.ravel(),
}).to_csv(os.path.join(OUT_TABLES, 'scheme_B_heatmap_grid.csv'), index=False)

print("  Tables saved.")


# ── 10. Figures ────────────────────────────────────────────────────────────────
print("\nGenerating figures …")
rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.unicode_minus'] = False

# ─ Figure 1: partial effects + heatmap + model comparison ─────────────────────
fig = plt.figure(figsize=(14, 10))
gs  = gridspec.GridSpec(2, 2, hspace=0.42, wspace=0.35)

# 1a: gestation partial effect
ax1 = fig.add_subplot(gs[0, 0])
ax1.scatter(df['孕周'], y, alpha=0.20, s=8, color='steelblue', label='Observations')
ax1.plot(g_grid, partial_g_pred, color='crimson', lw=2,
         label=f'Spline effect (deg={best_deg})')
ax1.fill_between(g_grid, ci_g_lo, ci_g_hi, color='crimson', alpha=0.18,
                 label='95% CI (group bootstrap)')
ax1.axhline(0.04, color='forestgreen', ls='--', lw=1.2, label='Threshold 4%')
ax1.set_xlabel('Gestational Week')
ax1.set_ylabel('Y Chrom. Concentration')
ax1.set_title('Partial Effect: Gestational Week')
ax1.legend(fontsize=7)
ax1.set_ylim(-0.01, 0.28)

# 1b: BMI partial effect
ax2 = fig.add_subplot(gs[0, 1])
ax2.scatter(df['孕妇BMI'], y, alpha=0.20, s=8, color='darkorange', label='Observations')
ax2.plot(b_grid, partial_b_pred, color='purple', lw=2,
         label=f'Spline effect (deg={best_deg})')
ax2.fill_between(b_grid, ci_b_lo, ci_b_hi, color='purple', alpha=0.18,
                 label='95% CI (group bootstrap)')
ax2.axhline(0.04, color='forestgreen', ls='--', lw=1.2, label='Threshold 4%')
ax2.set_xlabel('BMI')
ax2.set_ylabel('Y Chrom. Concentration')
ax2.set_title('Partial Effect: BMI')
ax2.legend(fontsize=7)
ax2.set_ylim(-0.01, 0.28)

# 1c: 2D heatmap
ax3 = fig.add_subplot(gs[1, 0])
cm  = ax3.contourf(g_hm, b_hm, Z_hm, levels=20, cmap='RdYlGn')
plt.colorbar(cm, ax=ax3, label='Y Conc (predicted, clipped≥0)')
ax3.set_xlabel('Gestational Week')
ax3.set_ylabel('BMI')
ax3.set_title('2D Heatmap: Predicted Y Concentration')

# 1d: model comparison bar chart
ax4 = fig.add_subplot(gs[1, 1])
labels_bar = ['Linear\n(deg=1)'] + [f'Spline\ndeg={d}' for d in DEGREES]
cv_rmses   = [lin_cv_rmse] + list(agg.sort_values('degree')['spline_cv_rmse_mean'])
colors_bar = ['#888888'] + ['steelblue'] * len(DEGREES)
bars = ax4.bar(labels_bar, cv_rmses, color=colors_bar, edgecolor='black', linewidth=0.7)
ax4.set_ylabel(f'{N_OUTER}-fold GroupKFold CV-RMSE')
ax4.set_title('Model Comparison (leak-free CV)')
best_bar_idx = int(np.argmin(cv_rmses))
bars[best_bar_idx].set_color('crimson')
ax4.set_ylim(0, max(cv_rmses) * 1.14)
for bar, val in zip(bars, cv_rmses):
    ax4.text(bar.get_x() + bar.get_width() / 2, val + 0.0001,
             f'{val:.4f}', ha='center', va='bottom', fontsize=7)

warn_str = f"Sanity warnings: {len(SANITY_LOG)}" if SANITY_LOG else "No sanity warnings"
fig.suptitle(
    f'Q1 Scheme B v2: Spline Regression – Leak-free CV\n'
    f'({warn_str})',
    fontsize=12, fontweight='bold'
)
fig.savefig(os.path.join(OUT_FIGS, 'scheme_B_raw.png'), dpi=150, bbox_inches='tight')
plt.close(fig)

# ─ Figure 2: residual diagnostics ─────────────────────────────────────────────
fig2, axes = plt.subplots(1, 3, figsize=(14, 4))

axes[0].scatter(y_pred, residuals, alpha=0.25, s=8, color='steelblue')
axes[0].axhline(0, color='red', lw=1)
axes[0].set_xlabel('Fitted values')
axes[0].set_ylabel('Residuals')
axes[0].set_title('Residuals vs Fitted')

axes[1].hist(residuals, bins=45, color='steelblue', edgecolor='white', alpha=0.8)
axes[1].set_xlabel('Residual')
axes[1].set_ylabel('Count')
axes[1].set_title(f'Residual Distribution\nShapiro p={p_shapiro:.2e}')

stats.probplot(residuals, plot=axes[2])
axes[2].set_title('Normal Q-Q Plot')

fig2.suptitle('Q1 Scheme B v2: Residual Analysis', fontsize=12, fontweight='bold')
fig2.tight_layout()
fig2.savefig(os.path.join(OUT_FIGS, 'scheme_B_residuals.png'), dpi=150, bbox_inches='tight')
plt.close(fig2)

print("  Figures saved.")


# ── 11. Summary ───────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("Q1 Scheme B v2 – Summary")
print("=" * 65)
print(f"Primary dataset:  {N} rows, {len(subject_codes)} subjects (<=25 weeks)")
print(f"Best spline deg:  {best_deg}   Alpha: {best_alpha_full}")
print(f"Train RMSE/R²:    {train_rmse:.5f} / {train_r2:.4f}")
print(f"Leak-free CV:")
print(f"  Spline   RMSE={sp_cv_rmse:.5f}  R²={sp_cv_r2:.4f}")
print(f"  Linear   RMSE={lin_cv_rmse:.5f}  R²={lin_cv_r2:.4f}")
print(f"  ΔRMSE (linear-spline) = {lin_cv_rmse-sp_cv_rmse:.5f}")
print(f"Gestation partial CI: [{ci_g_lo.min():.4f}, {ci_g_hi.max():.4f}]")
print(f"BMI partial CI:       [{ci_b_lo.min():.4f}, {ci_b_hi.max():.4f}]")
print(f"Residual Shapiro p: {p_shapiro:.2e}")
if SANITY_LOG:
    print(f"\nSanity warnings ({len(SANITY_LOG)}):")
    for w in SANITY_LOG:
        print(f"  {w}")
else:
    print("\nNo sanity warnings.")
print("=" * 65)
