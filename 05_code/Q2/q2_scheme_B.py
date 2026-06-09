"""
Q2 Scheme B v2 – Optimal BMI-based NIPT Timing via Dynamic Programming

Inherits Q1-B v2 confirmed model (degree=3, n_knots=5, alpha=88.5867).

Step 1: Estimate per-subject qualifying time T_i* (model-predicted: first week Y_hat >= 4%)
         + Empirical T_i* from actual observations (first observed week with Y >= 4%).
Step 2: DP-based 1D optimal BMI grouping for K=3,4,5,6 and min_size=20,30,40.
Step 3: Each group gets an optimal NIPT timing t_g minimising the risk function.
Step 4: Compare against empirical BMI baseline [20,28),[28,32),[32,36),[36,40),[40,+∞).
Step 5: Sensitivity analysis (K, min_size, c1/c2 weights, complexity penalty alpha).
Step 6: Bootstrap boundary stability (N=100).

Note on T_star degeneracy: For this high-BMI population, the Q1 model predicts
Y_hat >= 4% at week 10 for 266/267 subjects. This is a genuine data finding –
the high-BMI population studied can almost universally be screened at week 10.
The empirical T_star (from actual observations) is added as a secondary analysis
to show variation when some subjects had Y < 4% at early observation weeks.

Run from project root:
    python3 05_code/Q2/q2_scheme_B.py
"""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MPLCACHE = os.path.join(_REPO_ROOT, '.cache', 'matplotlib')
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

warnings.filterwarnings('ignore')
SEED = 42
np.random.seed(SEED)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = _REPO_ROOT
DATA_PATH = os.path.join(ROOT, '01_problem', 'source',
                         'CUMCM2025Problems', 'C题', '附件.xlsx')
OUT_TABLES = os.path.join(ROOT, '06_results', 'Q2', 'tables')
OUT_FIGS   = os.path.join(ROOT, '06_results', 'Q2', 'figures')
OUT_LOGS   = os.path.join(ROOT, '06_results', 'Q2', 'logs')
for d in [OUT_TABLES, OUT_FIGS, OUT_LOGS]:
    os.makedirs(d, exist_ok=True)

# ── Q1-B v2 confirmed model parameters ───────────────────────────────────────
BEST_DEG   = 3
N_KNOTS    = 5
BEST_ALPHA = 88.58667904100822   # from 06_results/Q1/tables/scheme_B_metrics.csv
N_INTER    = 3
THRESHOLD  = 0.04                # Y-chromosome concentration pass threshold

# Risk function default weights
C1_DEFAULT = 1.0   # per-subject early detection failure cost
C2_DEFAULT = 1.0   # late detection risk weight (multiplied by group size)

# NIPT timing candidates: half-week steps within clinical window (10-25 weeks)
T_CANDIDATES = np.arange(10.0, 25.5, 0.5)   # 31 values: 10, 10.5, ..., 25

# Bootstrap iterations
N_BOOT = 100

# QC columns (same as Q1-B v2)
QC_COLS = ['GC含量',
           '在参考基因组上比对的比例',
           '重复读段的比例',
           '被过滤掉读段数的比例']

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_gestation_week(s):
    """'12w+3' → 12.429; '13w' → 13.0"""
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


def weeks_to_wday(w):
    """12.5 → '12w+4d'; 13.0 → '13w'"""
    w = float(w)
    wk = int(w)
    days = int(round((w - wk) * 7))
    if days >= 7:
        wk += 1
        days = 0
    return f"{wk}w" if days == 0 else f"{wk}w+{days}d"


def build_features(g_col, b_col, qc_mat, sg, sb):
    """Replicate Q1-B v2 feature construction."""
    Xg = sg.transform(g_col)
    Xb = sb.transform(b_col)
    Xi = np.einsum('ij,ik->ijk',
                   Xg[:, :N_INTER],
                   Xb[:, :N_INTER]).reshape(len(g_col), -1)
    return np.hstack([Xg, Xb, Xi, qc_mat])


def late_risk_vec(t_arr):
    """
    Per-week late-detection risk (clinically motivated).
    r(t) = 0          for t <= 12  (early detection window intact)
    r(t) = (t-12)/13  for 12 < t <= 25  (linearly increases; 1.0 at week 25)
    r(t) = 1.0        for t > 25  (maximum risk beyond clinical window)
    """
    t = np.asarray(t_arr, dtype=float)
    r = np.where(t <= 12.0, 0.0, np.where(t <= 25.0, (t - 12.0) / 13.0, 1.0))
    return r


R_VEC = late_risk_vec(T_CANDIDATES)   # risk values for each timing candidate

# ── 1. Load & clean data ──────────────────────────────────────────────────────
print("Loading data …")
df_raw = pd.read_excel(DATA_PATH, sheet_name='男胎检测数据')
df_raw.columns = df_raw.columns.str.strip()
df_raw['孕周'] = df_raw['检测孕周'].apply(parse_gestation_week)

required = ['孕周', 'Y染色体浓度', '孕妇BMI', '孕妇代码']
df_base  = df_raw.dropna(subset=required).copy()
df_base  = df_base[(df_base['孕周'] >= 10) & (df_base['Y染色体浓度'] > 0)]
df       = df_base[df_base['孕周'] <= 25].reset_index(drop=True)

print(f"  Cleaned: {len(df)} rows, {df['孕妇代码'].nunique()} subjects")

y         = df['Y染色体浓度'].values
groups    = df['孕妇代码'].values
gestation = df['孕周'].values.reshape(-1, 1)
bmi_all   = df['孕妇BMI'].values.reshape(-1, 1)
qc_all    = df[QC_COLS].values

qc_global_med = np.nanmedian(qc_all, axis=0)

# Print Y concentration stats to understand the data
print(f"\n  Y concentration stats (all observations):")
print(f"    mean={np.mean(y):.4f}, median={np.median(y):.4f}")
print(f"    min={np.min(y):.4f}, max={np.max(y):.4f}")
print(f"    % >= 4%: {100*np.mean(y >= 0.04):.1f}%")

# Y concentration at 10-11 weeks specifically
mask_early = df['孕周'] <= 11
if mask_early.sum() > 0:
    y_early = y[mask_early]
    print(f"\n  Y concentration at 10-11w (n={mask_early.sum()}):")
    print(f"    mean={np.mean(y_early):.4f}, % >= 4%: {100*np.mean(y_early >= 0.04):.1f}%")


# ── 2. Re-fit Q1-B v2 model on full data ──────────────────────────────────────
print(f"\nRe-fitting Q1-B v2 (degree={BEST_DEG}, n_knots={N_KNOTS}, "
      f"alpha={BEST_ALPHA:.4f}) …")
spl_g = SplineTransformer(degree=BEST_DEG, n_knots=N_KNOTS, include_bias=False).fit(gestation)
spl_b = SplineTransformer(degree=BEST_DEG, n_knots=N_KNOTS, include_bias=False).fit(bmi_all)

X_full   = build_features(gestation, bmi_all, qc_all, spl_g, spl_b)
scaler   = StandardScaler().fit(X_full)
X_sc     = scaler.transform(X_full)
model    = Ridge(alpha=BEST_ALPHA).fit(X_sc, y)

y_pred   = model.predict(X_sc)
train_rmse = float(np.sqrt(np.mean((y - y_pred) ** 2)))
resid_std  = float(np.std(y - y_pred))
print(f"  Train RMSE={train_rmse:.5f}  resid_std={resid_std:.5f}  "
      f"(Q1 reference: RMSE=0.03151)")


# ── 3a. Model-predicted T_i* estimation ──────────────────────────────────────
print("\nEstimating model-predicted T_i* …")

RIGHT_CENSOR = 26.0   # used when 4% is never reached within 10-25 weeks

# Fine grid from 10 to 25 weeks
G_GRID = np.linspace(10.0, 25.0, 151)   # 0.1-week resolution

# Per-subject summary: mean BMI and median QC
subj_df = (df.groupby('孕妇代码')
             .agg(bmi=('孕妇BMI', 'mean'), n_obs=('孕周', 'count'))
             .reset_index())
qc_subj = (df.groupby('孕妇代码')[QC_COLS]
             .median()
             .reset_index())
subj_df = subj_df.merge(qc_subj, on='孕妇代码')

T_star_records = []
for _, row in subj_df.iterrows():
    b_val  = float(row['bmi'])
    qc_val = np.array([row[c] for c in QC_COLS], dtype=float)
    qc_val = np.where(np.isnan(qc_val), qc_global_med, qc_val)

    g_ = G_GRID.reshape(-1, 1)
    b_ = np.full_like(g_, b_val)
    qc_ = np.tile(qc_val, (len(G_GRID), 1))
    X_ = build_features(g_, b_, qc_, spl_g, spl_b)
    yhat = model.predict(scaler.transform(X_))

    cross = np.where(yhat >= THRESHOLD)[0]
    if len(cross) > 0:
        t_star   = float(G_GRID[cross[0]])
        censored = False
        yhat_at_t = float(yhat[cross[0]])
    else:
        t_star   = RIGHT_CENSOR
        censored = True
        yhat_at_t = float(yhat[-1])

    T_star_records.append({
        '孕妇代码':  row['孕妇代码'],
        'bmi':       b_val,
        'T_star':    t_star,
        'censored':  censored,
        'n_obs':     int(row['n_obs']),
        'yhat_at_Tstar': yhat_at_t,
    })

T_df = pd.DataFrame(T_star_records)
n_subj    = len(T_df)
n_censor  = int(T_df['censored'].sum())
pct_cens  = 100 * n_censor / n_subj

print(f"  {n_subj} subjects; censored={n_censor} ({pct_cens:.1f}%)")
print(f"  T_i* range: {T_df['T_star'].min():.2f} – {T_df['T_star'].max():.2f} weeks")
print(f"  T_i* median: {T_df['T_star'].median():.2f} weeks")
print(f"  T_i* == 10w: {(T_df['T_star'] == 10.0).sum()} subjects "
      f"({100*(T_df['T_star'] == 10.0).mean():.1f}%)")

T_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_individual_time.csv'), index=False)


# ── 3b. Empirical T_i* from actual observations ──────────────────────────────
print("\nEstimating empirical T_i* from actual observations …")

emp_T_star_records = []
for subj_code, grp in df.groupby('孕妇代码'):
    grp_sorted = grp.sort_values('孕周').reset_index(drop=True)
    bmi_val = float(grp_sorted['孕妇BMI'].mean())

    # Find first observation with Y >= 4%
    pass_mask = grp_sorted['Y染色体浓度'] >= THRESHOLD
    if pass_mask.any():
        first_pass_idx  = pass_mask.idxmax()
        emp_t_star      = float(grp_sorted.loc[first_pass_idx, '孕周'])
        emp_censored    = False
    else:
        # All observed Y < 4%; right-censor at max observed week
        emp_t_star   = float(grp_sorted['孕周'].max())
        emp_censored = True

    # Also record whether this woman had any pre-qualifying measurement (Y < 4%)
    n_fail_obs = int((grp_sorted['Y染色体浓度'] < THRESHOLD).sum())
    obs_min_y  = float(grp_sorted['Y染色体浓度'].min())
    obs_min_gest = float(grp_sorted.loc[grp_sorted['Y染色体浓度'].idxmin(), '孕周'])

    emp_T_star_records.append({
        '孕妇代码':     subj_code,
        'bmi':          bmi_val,
        'emp_T_star':   emp_t_star,
        'emp_censored': emp_censored,
        'n_fail_obs':   n_fail_obs,
        'obs_min_y':    obs_min_y,
        'obs_min_gest': obs_min_gest,
        'n_obs':        len(grp_sorted),
    })

emp_T_df = pd.DataFrame(emp_T_star_records)
# Merge with model T_star
T_df_full = T_df.merge(emp_T_df.drop(columns=['bmi', 'n_obs']), on='孕妇代码')

n_emp_censor = int(emp_T_df['emp_censored'].sum())
n_fail_any   = int((emp_T_df['n_fail_obs'] > 0).sum())
print(f"  Empirical T_star range: {emp_T_df['emp_T_star'].min():.2f} – "
      f"{emp_T_df['emp_T_star'].max():.2f} weeks")
print(f"  Empirical T_star median: {emp_T_df['emp_T_star'].median():.2f} weeks")
print(f"  Right-censored (never observed >=4%): {n_emp_censor} subjects")
print(f"  Subjects with any Y<4% observation: {n_fail_any} "
      f"({100*n_fail_any/n_subj:.1f}%)")

T_df_full.to_csv(os.path.join(OUT_TABLES, 'scheme_B_individual_time.csv'), index=False)
print("  scheme_B_individual_time.csv saved (with empirical T_star).")


# ── 4. DP cost precomputation helper ─────────────────────────────────────────

def precompute_cost_matrix(T_arr, c1, c2):
    """
    Returns cost[i, j] = min-risk and opt_t[i, j] for group T_arr[i:j].
    Vectorised over timing candidates.

    Risk for group g = c1 * (# subjects with T_i* > t_g) + c2 * n_g * r(t_g)
    Where n_g = j - i is the group size.
    """
    n = len(T_arr)
    cost  = np.full((n, n + 1), np.inf)
    opt_t = np.full((n, n + 1), np.nan)

    for i in range(n):
        cum_fail = np.zeros(len(T_CANDIDATES))
        for k in range(1, n - i + 1):
            j = i + k
            # Subjects with T_i* > each candidate timing (early-detection failure)
            cum_fail += (T_arr[j - 1] > T_CANDIDATES).astype(float)
            # Risk = c1*early_failures + c2*group_size*r(t)
            risks = c1 * cum_fail + c2 * k * R_VEC
            best  = int(np.argmin(risks))
            cost[i, j]  = risks[best]
            opt_t[i, j] = T_CANDIDATES[best]

    return cost, opt_t


def dp_split(T_arr_sorted, K, min_size, cost_mat, opt_t_mat):
    """
    DP: dp[k, j] = min total risk for first j subjects split into k groups.
    Returns (group_list, total_risk) or None if infeasible.
    """
    n  = len(T_arr_sorted)
    INF = 1e18

    if K * min_size > n:
        return None

    dp    = np.full((K + 1, n + 1), INF)
    split = np.full((K + 1, n + 1), -1, dtype=int)
    dp[0, 0] = 0.0

    for k in range(1, K + 1):
        i_lo = (k - 1) * min_size
        for j in range(k * min_size, n + 1):
            i_hi = j - min_size
            if i_lo > i_hi:
                continue
            prev   = dp[k - 1, i_lo:i_hi + 1]
            g_cost = cost_mat[i_lo:i_hi + 1, j]
            total  = prev + g_cost
            best   = int(np.argmin(total))
            if total[best] < dp[k, j]:
                dp[k, j]    = total[best]
                split[k, j] = i_lo + best

    if dp[K, n] >= INF:
        return None

    # Backtrack
    groups = []
    j = n
    for k in range(K, 0, -1):
        i = split[k, j]
        groups.append({
            'group_idx':      k,
            'start_idx':      int(i),
            'end_idx':        int(j),
            'n':              int(j - i),
            'optimal_t':      float(opt_t_mat[i, j]),
            'optimal_t_wday': weeks_to_wday(opt_t_mat[i, j]),
            'group_risk':     float(cost_mat[i, j]),
        })
        j = i

    groups = sorted(groups, key=lambda x: x['group_idx'])
    return groups, float(dp[K, n])


def enrich_groups(groups, bmi_sorted, T_sorted):
    """Add BMI boundaries and T_i* stats to group dicts."""
    for g in groups:
        i, j = g['start_idx'], g['end_idx']
        b_seg = bmi_sorted[i:j]
        T_seg = T_sorted[i:j]
        g.update({
            'bmi_lo':        float(b_seg[0]),
            'bmi_hi':        float(b_seg[-1]),
            'n_early_fail':  int(np.sum(T_seg > g['optimal_t'])),
            'n_censored':    int(np.sum(np.isclose(T_seg, RIGHT_CENSOR))),
            'T_star_mean':   float(np.mean(T_seg)),
            'T_star_median': float(np.median(T_seg)),
            'T_star_p25':    float(np.percentile(T_seg, 25)),
            'T_star_p75':    float(np.percentile(T_seg, 75)),
        })
    return groups


# ── 5. Main DP runs: K=3,4,5,6 × min_size=20,30,40 ──────────────────────────
print("\nRunning dynamic programming grouping (model-predicted T_star) …")

T_sorted   = T_df.sort_values('bmi').reset_index(drop=True)
bmi_sorted = T_sorted['bmi'].values
T_arr      = T_sorted['T_star'].values

# Precompute cost matrix with default weights (reused for all K/min_size)
print("  Precomputing cost matrix (default c1=1, c2=1) …")
cost_default, opt_t_default = precompute_cost_matrix(T_arr, C1_DEFAULT, C2_DEFAULT)
print("  Done.")

K_VALUES  = [3, 4, 5, 6]
MIN_SIZES = [20, 30, 40]

all_summary  = []
groups_store = {}   # (K, min_size) → (groups, total_risk)

for K in K_VALUES:
    for ms in MIN_SIZES:
        res = dp_split(T_arr, K, ms, cost_default, opt_t_default)
        if res is None:
            print(f"  K={K}, min_size={ms}: infeasible")
            continue
        grps, total_risk = res
        grps = enrich_groups(grps, bmi_sorted, T_arr)
        groups_store[(K, ms)] = (grps, total_risk)

        bmi_cuts = [grps[0]['bmi_lo']] + [g['bmi_hi'] for g in grps]
        cuts_str = ', '.join(f"{b:.1f}" for b in bmi_cuts)
        timings  = ', '.join(g['optimal_t_wday'] for g in grps)
        print(f"  K={K}, min_size={ms}: risk={total_risk:.3f}  "
              f"cuts=[{cuts_str}]  timing=[{timings}]")

        for g in grps:
            row = {'K': K, 'min_size': ms, 'c1': C1_DEFAULT, 'c2': C2_DEFAULT,
                   'alpha_penalty': 0.0, 'total_risk': total_risk}
            row.update(g)
            all_summary.append(row)

metrics_df = pd.DataFrame(all_summary)
metrics_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_metrics.csv'), index=False)
print("  scheme_B_metrics.csv saved.")


# ── 6. Select optimal K (default min_size=30) ────────────────────────────────
k_risks = {}
for K in K_VALUES:
    if (K, 30) in groups_store:
        _, tr = groups_store[(K, 30)]
        k_risks[K] = tr

best_K = min(k_risks, key=k_risks.get)
print(f"\nK selection (min_size=30, no complexity penalty):")
for K, r in sorted(k_risks.items()):
    tag = " ← best" if K == best_K else ""
    print(f"  K={K}: total_risk={r:.3f}{tag}")

best_groups, best_total_risk = groups_store[(best_K, 30)]

# Save best grouping table
group_rows = []
for g in best_groups:
    g_copy = dict(g)
    g_copy['K'] = best_K
    g_copy['min_size'] = 30
    g_copy['total_risk'] = best_total_risk
    group_rows.append(g_copy)
best_groups_df = pd.DataFrame(group_rows)
best_groups_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_group_timing.csv'), index=False)
print("  scheme_B_group_timing.csv saved.")


# ── 7. Empirical BMI baseline (fixed cuts: [20,28),[28,32),[32,36),[36,40),[40,+∞)) ──
print("\nComputing empirical BMI baseline …")

# Note: problem statement example uses [20,28),[28,32),[32,36),[36,40),[40,+∞)
EMP_CUTS   = [20, 28, 32, 36, 40, 200]
EMP_LABELS = ['[20,28)', '[28,32)', '[32,36)', '[36,40)', '[40,+∞)']

emp_rows = []
for idx, label in enumerate(EMP_LABELS):
    lo, hi = EMP_CUTS[idx], EMP_CUTS[idx + 1]
    mask   = (bmi_sorted >= lo) & (bmi_sorted < hi)
    T_seg  = T_arr[mask]
    if len(T_seg) == 0:
        emp_rows.append({'group_label': label, 'bmi_range': f'[{lo},{hi})',
                         'n': 0, 'optimal_t': np.nan, 'optimal_t_wday': '-',
                         'group_risk': np.nan, 'n_early_fail': np.nan,
                         'T_star_mean': np.nan, 'T_star_median': np.nan})
        continue
    risks   = C1_DEFAULT * np.sum(T_seg[:, None] > T_CANDIDATES, axis=0) \
            + C2_DEFAULT * len(T_seg) * R_VEC
    best_i  = int(np.argmin(risks))
    opt_t   = float(T_CANDIDATES[best_i])
    emp_rows.append({
        'group_label':   label,
        'bmi_range':     f'[{lo},{hi})',
        'n':             len(T_seg),
        'optimal_t':     opt_t,
        'optimal_t_wday':weeks_to_wday(opt_t),
        'group_risk':    float(risks[best_i]),
        'n_early_fail':  int(np.sum(T_seg > opt_t)),
        'T_star_mean':   float(np.mean(T_seg)),
        'T_star_median': float(np.median(T_seg)),
        'T_star_p25':    float(np.percentile(T_seg, 25)),
        'T_star_p75':    float(np.percentile(T_seg, 75)),
    })
    print(f"  {label}: n={len(T_seg)}, t*={weeks_to_wday(opt_t)}, "
          f"T_star_mean={np.mean(T_seg):.2f}, risk={risks[best_i]:.3f}")

emp_df = pd.DataFrame(emp_rows)
emp_total_risk = float(emp_df['group_risk'].sum(skipna=True))
emp_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_empirical_baseline.csv'), index=False)
print(f"  Empirical total risk: {emp_total_risk:.3f}")
print(f"  DP (K={best_K}) total risk: {best_total_risk:.3f}")
if emp_total_risk > 0:
    risk_reduct = 100 * (emp_total_risk - best_total_risk) / emp_total_risk
else:
    risk_reduct = 0.0
print(f"  Risk reduction: {risk_reduct:.1f}%")
print("  scheme_B_empirical_baseline.csv saved.")


# ── 7b. Empirical T_star DP grouping (secondary analysis) ────────────────────
print("\nDP grouping with empirical T_star (secondary analysis) …")

emp_T_sorted = emp_T_df.sort_values('bmi').reset_index(drop=True)
bmi_emp_sorted = emp_T_sorted['bmi'].values
# Use min(emp_T_star, 25) as the qualifying time; cap at 25 to avoid inflated risk
T_emp_arr = np.minimum(emp_T_sorted['emp_T_star'].values, 25.0)

# Precompute cost matrix for empirical T_star
cost_emp, opt_t_emp = precompute_cost_matrix(T_emp_arr, C1_DEFAULT, C2_DEFAULT)

emp_dp_rows = []
for K in K_VALUES:
    for ms in MIN_SIZES:
        res = dp_split(T_emp_arr, K, ms, cost_emp, opt_t_emp)
        if res is None:
            continue
        grps, total_risk = res
        grps = enrich_groups(grps, bmi_emp_sorted, T_emp_arr)
        bmi_cuts = [grps[0]['bmi_lo']] + [g['bmi_hi'] for g in grps]
        cuts_str = ', '.join(f"{b:.1f}" for b in bmi_cuts)
        timings  = ', '.join(g['optimal_t_wday'] for g in grps)
        print(f"  [EMP] K={K}, min_size={ms}: risk={total_risk:.3f}  "
              f"cuts=[{cuts_str}]  timing=[{timings}]")
        for g in grps:
            row = {'source': 'empirical', 'K': K, 'min_size': ms,
                   'total_risk': total_risk}
            row.update(g)
            emp_dp_rows.append(row)

emp_dp_df = pd.DataFrame(emp_dp_rows)
emp_dp_df.to_csv(
    os.path.join(OUT_TABLES, 'scheme_B_empirical_tstar_grouping.csv'), index=False)
print("  scheme_B_empirical_tstar_grouping.csv saved.")


# ── 8. Sensitivity analysis ───────────────────────────────────────────────────
print("\nRunning sensitivity analysis …")
sens_rows = []

# 8a: K × min_size (already computed)
for K in K_VALUES:
    for ms in MIN_SIZES:
        if (K, ms) in groups_store:
            _, total_risk = groups_store[(K, ms)]
            sens_rows.append({'scenario': f'K={K}_minsize={ms}',
                              'param_type': 'K_minsize',
                              'K': K, 'min_size': ms,
                              'c1': C1_DEFAULT, 'c2': C2_DEFAULT,
                              'alpha_penalty': 0.0,
                              'total_risk': total_risk,
                              'best_K_selected': K})

# 8b: Weight sensitivity (c1, c2) – recompute cost matrix each time
for c1v in [0.5, 1.0, 2.0]:
    for c2v in [0.5, 1.0, 2.0]:
        if c1v == C1_DEFAULT and c2v == C2_DEFAULT:
            continue  # covered in K×min_size block
        print(f"  Weight c1={c1v}, c2={c2v} …")
        cost_w, opt_t_w = precompute_cost_matrix(T_arr, c1v, c2v)
        best_risk_w = np.inf
        best_K_w    = K_VALUES[0]
        for K in K_VALUES:
            res = dp_split(T_arr, K, 30, cost_w, opt_t_w)
            if res is not None:
                _, tr = res
                if tr < best_risk_w:
                    best_risk_w = tr
                    best_K_w    = K
        sens_rows.append({'scenario': f'c1={c1v}_c2={c2v}',
                          'param_type': 'weights',
                          'K': best_K_w, 'min_size': 30,
                          'c1': c1v, 'c2': c2v,
                          'alpha_penalty': 0.0,
                          'total_risk': best_risk_w,
                          'best_K_selected': best_K_w})

# 8c: Complexity penalty alpha
for ap in [0.0, 5.0, 10.0, 20.0]:
    best_obj = np.inf
    best_K_a = K_VALUES[0]
    for K in K_VALUES:
        if (K, 30) in groups_store:
            _, tr = groups_store[(K, 30)]
            obj = tr + ap * K
            if obj < best_obj:
                best_obj = obj
                best_K_a = K
    sens_rows.append({'scenario': f'alpha={ap}',
                      'param_type': 'complexity_penalty',
                      'K': best_K_a, 'min_size': 30,
                      'c1': C1_DEFAULT, 'c2': C2_DEFAULT,
                      'alpha_penalty': ap,
                      'total_risk': best_obj,
                      'best_K_selected': best_K_a})

sens_df = pd.DataFrame(sens_rows)
sens_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_boundary_sensitivity.csv'), index=False)
print("  scheme_B_boundary_sensitivity.csv saved.")


# ── 9. Bootstrap boundary stability ──────────────────────────────────────────
print(f"\nBootstrap boundary stability (N={N_BOOT}) …")
all_codes = T_df['孕妇代码'].values
boot_rows = []
boot_failed = 0

for i_b in range(N_BOOT):
    rng   = np.random.RandomState(SEED + i_b)
    codes = rng.choice(all_codes, size=len(all_codes), replace=True)

    T_boot = (T_df.set_index('孕妇代码')
                  .loc[codes]
                  .reset_index()
                  .sort_values('bmi')
                  .reset_index(drop=True))
    bmi_b = T_boot['bmi'].values
    T_b   = T_boot['T_star'].values

    cost_b, opt_t_b = precompute_cost_matrix(T_b, C1_DEFAULT, C2_DEFAULT)
    res = dp_split(T_b, best_K, 30, cost_b, opt_t_b)
    if res is None:
        boot_failed += 1
        continue

    grps_b, _ = res
    grps_b = enrich_groups(grps_b, bmi_b, T_b)
    row = {'boot_i': i_b}
    for g in grps_b:
        gi = g['group_idx']
        row[f'bmi_lo_g{gi}']  = g['bmi_lo']
        row[f'bmi_hi_g{gi}']  = g['bmi_hi']
        row[f'opt_t_g{gi}']   = g['optimal_t']
        row[f'risk_g{gi}']    = g['group_risk']
    boot_rows.append(row)

boot_df = pd.DataFrame(boot_rows)
print(f"  Bootstrap done: {len(boot_rows)} valid / {N_BOOT} total "
      f"({boot_failed} failed)")

# Boundary stability stats
stab_rows = []
for gi in range(1, best_K + 1):
    lo_col = f'bmi_lo_g{gi}'
    hi_col = f'bmi_hi_g{gi}'
    t_col  = f'opt_t_g{gi}'
    r_col  = f'risk_g{gi}'
    if lo_col in boot_df.columns:
        stab_rows.append({
            'group':        gi,
            'bmi_lo_mean':  float(boot_df[lo_col].mean()),
            'bmi_lo_std':   float(boot_df[lo_col].std()),
            'bmi_hi_mean':  float(boot_df[hi_col].mean()),
            'bmi_hi_std':   float(boot_df[hi_col].std()),
            'opt_t_mean':   float(boot_df[t_col].mean()),
            'opt_t_std':    float(boot_df[t_col].std()),
            'risk_mean':    float(boot_df[r_col].mean()),
            'risk_std':     float(boot_df[r_col].std()),
        })

stab_df = pd.DataFrame(stab_rows)
stab_df.to_csv(os.path.join(OUT_TABLES, 'scheme_B_bootstrap_stability.csv'), index=False)
print("  scheme_B_bootstrap_stability.csv saved.")


# ── 10. Figures ───────────────────────────────────────────────────────────────
print("\nGenerating figures …")
rcParams['font.family'] = 'DejaVu Sans'
rcParams['axes.unicode_minus'] = False

GROUP_COLORS = ['#e74c3c', '#e67e22', '#2ecc71', '#3498db',
                '#9b59b6', '#1abc9c']

# ─ Figure 1: T_i* scatter + boxplots + empirical T_star (scheme_B_raw.png) ───
fig = plt.figure(figsize=(16, 10))
gs  = gridspec.GridSpec(2, 2, hspace=0.40, wspace=0.38)

# 1a: Model-predicted T_star scatter vs BMI
ax1 = fig.add_subplot(gs[0, 0])
ax1.scatter(bmi_sorted, T_arr, alpha=0.40, s=20, c='steelblue',
            label='Model T_i* per subject', zorder=2)
for g in best_groups:
    c = GROUP_COLORS[(g['group_idx'] - 1) % len(GROUP_COLORS)]
    ax1.axvline(g['bmi_hi'], color='dimgray', ls='--', lw=1.2, alpha=0.7, zorder=3)
    ax1.axhline(g['optimal_t'], color=c, ls='-', lw=1.8, alpha=0.75,
                label=f"G{g['group_idx']} t*={g['optimal_t_wday']}", zorder=3)
    mid = (g['bmi_lo'] + g['bmi_hi']) / 2
    ax1.text(mid, g['optimal_t'] + 0.5, f"G{g['group_idx']}", ha='center',
             fontsize=9, color=c, fontweight='bold')

ax1.axhline(12.0, color='forestgreen', ls=':', lw=1.2, alpha=0.6, label='12w midterm')
ax1.set_xlabel('Maternal BMI')
ax1.set_ylabel('Qualifying Time T_i* (weeks, model)')
ax1.set_title(f'Model-Predicted T_i* vs BMI\n(K={best_K} optimal grouping, '
              f'c1=c2=1)')
ax1.legend(fontsize=7, loc='upper right')
ax1.set_ylim(8, 28)
ax1.set_xlim(18, 50)

# 1b: Empirical T_star scatter vs BMI
ax2 = fig.add_subplot(gs[0, 1])
emp_bmi   = emp_T_df['bmi'].values
emp_t_arr = np.minimum(emp_T_df['emp_T_star'].values, 25.0)
emp_fail  = emp_T_df['n_fail_obs'].values > 0
ax2.scatter(emp_bmi[~emp_fail], emp_t_arr[~emp_fail],
            alpha=0.40, s=20, c='steelblue',
            label='Always Y≥4%', zorder=2)
ax2.scatter(emp_bmi[emp_fail], emp_t_arr[emp_fail],
            alpha=0.55, s=30, c='crimson', marker='x',
            label='Had Y<4% obs', zorder=3)
for cut, label in zip(EMP_CUTS[1:-1], EMP_LABELS[:-1]):
    ax2.axvline(cut, color='dimgray', ls='--', lw=1.0, alpha=0.6)
ax2.axhline(12.0, color='forestgreen', ls=':', lw=1.2, alpha=0.6, label='12w midterm')
ax2.set_xlabel('Maternal BMI')
ax2.set_ylabel('Empirical Qualifying Time (weeks)')
ax2.set_title('Empirical T_i* from Actual Observations\n'
              '(first week with observed Y≥4%)')
ax2.legend(fontsize=7, loc='upper right')
ax2.set_ylim(8, 28)
ax2.set_xlim(18, 50)

# 1c: Boxplot of model T_star per optimal group
ax3 = fig.add_subplot(gs[1, 0])
box_data   = []
box_labels = []
for g in best_groups:
    mask = (bmi_sorted >= g['bmi_lo']) & (bmi_sorted <= g['bmi_hi'])
    box_data.append(T_arr[mask])
    label = f"G{g['group_idx']}\nBMI [{g['bmi_lo']:.0f},{g['bmi_hi']:.0f}]"
    box_labels.append(label)

bps = ax3.boxplot(box_data, labels=box_labels, patch_artist=True,
                  notch=False, widths=0.6)
for patch, c in zip(bps['boxes'], GROUP_COLORS[:len(box_data)]):
    patch.set_facecolor(c)
    patch.set_alpha(0.55)
ax3.axhline(12.0, color='forestgreen', ls='--', lw=1.5, label='12w threshold')
ax3.axhline(10.0, color='navy', ls=':', lw=1.2, alpha=0.7, label='10w earliest')
ax3.set_xlabel('BMI Group')
ax3.set_ylabel('Model T_i* (weeks)')
ax3.set_title(f'T_i* Distribution per BMI Group (K={best_K})')
ax3.legend(fontsize=8)
ax3.set_ylim(8, 28)

# 1d: Empirical baseline comparison bar chart
ax4 = fig.add_subplot(gs[1, 1])
valid_emp = emp_df[emp_df['n'] > 0].copy()
x_pos     = np.arange(len(valid_emp))
w         = 0.35
t_vals    = valid_emp['optimal_t'].values
# DP best group timings – match to empirical BMI ranges
ax4.bar(x_pos - w/2, t_vals, w, label='Empirical BMI grouping t*',
        color='#95a5a6', edgecolor='black', linewidth=0.6)
ax4.axhline(10.0, color='navy', ls='--', lw=1.2, alpha=0.8, label='10w (earliest)')
ax4.axhline(12.0, color='forestgreen', ls='--', lw=1.2, alpha=0.8, label='12w (midterm)')
ax4.set_xticks(x_pos - w/2)
ax4.set_xticklabels(valid_emp['group_label'].values, rotation=15, ha='right', fontsize=8)
ax4.set_ylabel('Optimal NIPT Timing t* (weeks)')
ax4.set_title('Empirical BMI Grouping:\nOptimal NIPT Timing per Group')
ax4.legend(fontsize=8)
ax4.set_ylim(8, 16)

fig.suptitle(
    f'Q2 Scheme B: Optimal BMI-Based NIPT Timing (K={best_K}, c1=c2=1)\n'
    f'Model-predicted T_i* vs Empirical T_i* comparison',
    fontsize=12, fontweight='bold')
fig.savefig(os.path.join(OUT_FIGS, 'scheme_B_raw.png'), dpi=150, bbox_inches='tight')
plt.close(fig)
print("  scheme_B_raw.png saved.")


# ─ Figure 2: BMI boundaries + bootstrap stability (scheme_B_boundaries.png) ──
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))

# Left: total risk vs K for different min_sizes
ax_l = axes2[0]
for ms in MIN_SIZES:
    ks_ = [K for K in K_VALUES if (K, ms) in groups_store]
    rs_ = [groups_store[(K, ms)][1] for K in ks_]
    if ks_:
        ax_l.plot(ks_, rs_, marker='o', label=f'min_size={ms}')

ax_l.axvline(best_K, color='red', ls='--', lw=1.5, label=f'Best K={best_K}')
ax_l.set_xlabel('Number of Groups K')
ax_l.set_ylabel('Total Risk (model T_i*)')
ax_l.set_title(f'Total Risk vs K\n(default c1=c2=1, min_size varied)')
ax_l.legend(fontsize=8)
ax_l.grid(True, alpha=0.3)
ax_l.set_xticks(K_VALUES)

# Right: bootstrap BMI boundary distributions
ax_r = axes2[1]
if len(boot_df) > 5:
    for gi in range(1, best_K):
        col = f'bmi_hi_g{gi}'
        if col in boot_df.columns:
            data = boot_df[col].dropna()
            if len(data) > 5:
                ax_r.hist(data, bins=25, alpha=0.55,
                          label=f'Boundary G{gi}|G{gi+1}',
                          color=GROUP_COLORS[(gi - 1) % len(GROUP_COLORS)])
    ax_r.set_xlabel('BMI Boundary Value')
    ax_r.set_ylabel('Bootstrap Count')
    ax_r.set_title(f'Bootstrap BMI Boundary Distribution\n'
                   f'(K={best_K}, n={len(boot_df)} iterations)')
    ax_r.legend(fontsize=8)
else:
    ax_r.text(0.5, 0.5, 'Insufficient bootstrap data', transform=ax_r.transAxes,
              ha='center', va='center')

fig2.suptitle('Q2 Scheme B: DP Grouping Sensitivity and Boundary Stability',
              fontsize=12, fontweight='bold')
fig2.tight_layout()
fig2.savefig(os.path.join(OUT_FIGS, 'scheme_B_boundaries.png'), dpi=150, bbox_inches='tight')
plt.close(fig2)
print("  scheme_B_boundaries.png saved.")


# ─ Figure 3: Sensitivity (scheme_B_sensitivity.png) ──────────────────────────
fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5))

# Left: weight sensitivity heatmap
ax3l = axes3[0]
c1_vals = [0.5, 1.0, 2.0]
c2_vals = [0.5, 1.0, 2.0]
heat_risk = np.zeros((3, 3))
for i_c1, c1v in enumerate(c1_vals):
    for i_c2, c2v in enumerate(c2_vals):
        subset = sens_df[(np.isclose(sens_df['c1'], c1v))
                         & (np.isclose(sens_df['c2'], c2v))
                         & (sens_df['param_type'].isin(['weights', 'K_minsize']))]
        if len(subset) > 0:
            heat_risk[i_c1, i_c2] = float(subset['total_risk'].mean())
        else:
            if np.isclose(c1v, 1.0) and np.isclose(c2v, 1.0):
                heat_risk[i_c1, i_c2] = best_total_risk
            else:
                heat_risk[i_c1, i_c2] = np.nan

im = ax3l.imshow(heat_risk, aspect='auto', cmap='RdYlGn_r',
                  vmin=np.nanmin(heat_risk), vmax=np.nanmax(heat_risk))
fig3.colorbar(im, ax=ax3l, label='Total Risk')
ax3l.set_xticks(range(3))
ax3l.set_yticks(range(3))
ax3l.set_xticklabels([f'c2={v}' for v in c2_vals])
ax3l.set_yticklabels([f'c1={v}' for v in c1_vals])
ax3l.set_title('Risk Sensitivity to Weights (c1, c2)\n(K auto-selected, min_size=30)')
for i in range(3):
    for j in range(3):
        val = heat_risk[i, j]
        if not np.isnan(val):
            ax3l.text(j, i, f'{val:.2f}', ha='center', va='center',
                      fontsize=9, color='black')

# Right: complexity penalty effect on K selection
ax3r = axes3[1]
alpha_subset = sens_df[sens_df['param_type'] == 'complexity_penalty'].copy()
if len(alpha_subset) > 0:
    ax3r.plot(alpha_subset['alpha_penalty'], alpha_subset['total_risk'],
              marker='o', color='steelblue', label='Objective (risk + α·K)')
    ax3r_twin = ax3r.twinx()
    ax3r_twin.step(alpha_subset['alpha_penalty'], alpha_subset['best_K_selected'],
                   color='crimson', lw=1.5, where='mid', label='Optimal K')
    ax3r_twin.set_ylabel('Optimal K', color='crimson')
    ax3r_twin.tick_params(axis='y', colors='crimson')
    ax3r_twin.set_yticks(K_VALUES)
    ax3r.set_xlabel('Complexity Penalty α')
    ax3r.set_ylabel('Total Objective Value')
    ax3r.set_title('K Selection vs Complexity Penalty α\n(min_size=30, c1=c2=1)')
    l1, lb1 = ax3r.get_legend_handles_labels()
    l2, lb2 = ax3r_twin.get_legend_handles_labels()
    ax3r.legend(l1 + l2, lb1 + lb2, fontsize=8)
    ax3r.grid(True, alpha=0.3)

fig3.suptitle('Q2 Scheme B: Sensitivity Analysis (model-predicted T_i*)',
              fontsize=12, fontweight='bold')
fig3.tight_layout()
fig3.savefig(os.path.join(OUT_FIGS, 'scheme_B_sensitivity.png'), dpi=150, bbox_inches='tight')
plt.close(fig3)
print("  scheme_B_sensitivity.png saved.")


# ── 11. Print summary ─────────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("Q2 Scheme B v2 – Summary")
print("=" * 72)
print(f"Dataset      : {len(df)} rows, {n_subj} subjects (<=25 weeks)")
print(f"BMI range    : {bmi_sorted.min():.1f} – {bmi_sorted.max():.1f}")
print(f"\n[Model-predicted T_star]")
print(f"  Range      : {T_df['T_star'].min():.2f} – {T_df['T_star'].max():.2f} weeks")
print(f"  T==10w     : {(T_df['T_star'] == 10.0).sum()}/{n_subj} subjects "
      f"({100*(T_df['T_star'] == 10.0).mean():.0f}%)")
print(f"  Censored   : {n_censor} ({pct_cens:.1f}%)")

print(f"\n[Empirical T_star]")
print(f"  Range      : {emp_T_df['emp_T_star'].min():.2f} – "
      f"{emp_T_df['emp_T_star'].max():.2f} weeks")
print(f"  Median     : {emp_T_df['emp_T_star'].median():.2f} weeks")
print(f"  Right-censored : {n_emp_censor}")
print(f"  Had Y<4% obs   : {n_fail_any} subjects "
      f"({100*n_fail_any/n_subj:.1f}%)")

print(f"\n[DP Grouping (model T_star, K={best_K}, min_size=30, c1=c2=1)]")
for g in best_groups:
    print(f"  G{g['group_idx']}: BMI [{g['bmi_lo']:.1f}, {g['bmi_hi']:.1f}]  "
          f"n={g['n']}  t*={g['optimal_t']:.1f}w ({g['optimal_t_wday']})  "
          f"T*_mean={g['T_star_mean']:.2f}  risk={g['group_risk']:.3f}")
print(f"\n  DP total risk (K={best_K}) : {best_total_risk:.3f}")
print(f"  Empirical total risk      : {emp_total_risk:.3f}")
print(f"  Risk reduction            : {risk_reduct:.1f}%")

print(f"\n[Boundary stability (bootstrap n={len(boot_rows)})]")
if len(stab_df) > 0:
    for _, row in stab_df.iterrows():
        print(f"  G{int(row.group)}: BMI_hi = {row.bmi_hi_mean:.2f} ± {row.bmi_hi_std:.2f}  "
              f"t* = {row.opt_t_mean:.2f} ± {row.opt_t_std:.2f} weeks")
print("=" * 72)


# ── 12. Write run log ─────────────────────────────────────────────────────────
emp_t_min = float(emp_T_df['emp_T_star'].min())
emp_t_max = float(emp_T_df['emp_T_star'].max())
emp_t_med = float(emp_T_df['emp_T_star'].median())

run_log = f"""# Q2 Scheme B Run Log (v2)

## Run Information
- Date: 2026-06-09
- Script: 05_code/Q2/q2_scheme_B.py
- Run command: `python3 05_code/Q2/q2_scheme_B.py` (from project root)
- Random seed: {SEED}

## Q1-B v2 Parameters Inherited
- best_degree: {BEST_DEG}
- n_knots: {N_KNOTS}
- alpha: {BEST_ALPHA}
- resid_std: {resid_std:.5f}
- Source: 06_results/Q1/tables/scheme_B_metrics.csv

## Input Files
- 01_problem/source/CUMCM2025Problems/C题/附件.xlsx (sheet: 男胎检测数据)
- 05_code/Q1/q1_scheme_B.py (feature engineering reference)
- 06_results/Q1/tables/scheme_B_metrics.csv (confirmed Q1 model params)

## Data
- Cleaned rows: {len(df)}
- Subjects: {n_subj}
- Y concentration (all obs): mean={np.mean(y):.4f}, >=4%={100*np.mean(y>=0.04):.1f}%

## Model-Predicted T_i*
- Censored (T_i*=26w): {n_censor} ({pct_cens:.1f}%)
- T_i* range: {T_df['T_star'].min():.2f} – {T_df['T_star'].max():.2f} weeks
- T_i* == 10w: {(T_df['T_star'] == 10.0).sum()}/{n_subj} ({100*(T_df['T_star'] == 10.0).mean():.0f}%)
- Note: T_i* degeneracy – Q1 model predicts Y_hat >= 4% at week 10 for nearly all
  subjects. This reflects the high-BMI population studied (most BMI 28-40) where
  Y concentration is generally above 4% at the start of the clinical window.

## Empirical T_i* (from actual observations)
- Range: {emp_t_min:.2f} – {emp_t_max:.2f} weeks
- Median: {emp_t_med:.2f} weeks
- Right-censored: {n_emp_censor} subjects (never observed Y >= 4%)
- Subjects with any Y<4% obs: {n_fail_any} ({100*n_fail_any/n_subj:.1f}%)

## Key Results
- Best K: {best_K} (selected by min total risk, min_size=30)
- DP total risk (model T_i*): {best_total_risk:.3f}
- Empirical BMI grouping total risk: {emp_total_risk:.3f}
- Risk reduction: {risk_reduct:.1f}%

## Grouping (K={best_K}, model T_i*)
| Group | BMI Range | n | t* | t* (w+d) | T*_mean | Risk |
|-------|-----------|---|------|----------|---------|------|
""" + "\n".join(
    f"| G{g['group_idx']} | [{g['bmi_lo']:.1f}, {g['bmi_hi']:.1f}] | {g['n']} "
    f"| {g['optimal_t']:.1f}w | {g['optimal_t_wday']} "
    f"| {g['T_star_mean']:.2f}w | {g['group_risk']:.3f} |"
    for g in best_groups
) + f"""

## Empirical BMI Grouping
| Group | n | t* | t* (w+d) | T*_mean | Risk |
|-------|---|------|----------|---------|------|
""" + "\n".join(
    f"| {r['group_label']} | {int(r['n'])} "
    f"| {r['optimal_t']:.1f}w | {r['optimal_t_wday']} "
    f"| {r['T_star_mean']:.2f}w | {r['group_risk']:.3f} |"
    for _, r in emp_df[emp_df['n'] > 0].iterrows()
) + f"""

## Output Files
- 06_results/Q2/tables/scheme_B_individual_time.csv
- 06_results/Q2/tables/scheme_B_group_timing.csv
- 06_results/Q2/tables/scheme_B_metrics.csv
- 06_results/Q2/tables/scheme_B_boundary_sensitivity.csv
- 06_results/Q2/tables/scheme_B_empirical_baseline.csv
- 06_results/Q2/tables/scheme_B_empirical_tstar_grouping.csv
- 06_results/Q2/tables/scheme_B_bootstrap_stability.csv
- 06_results/Q2/figures/scheme_B_raw.png
- 06_results/Q2/figures/scheme_B_boundaries.png
- 06_results/Q2/figures/scheme_B_sensitivity.png
- 06_results/Q2/logs/scheme_B_run.md

## Bootstrap Stability
- Iterations: {len(boot_rows)}/{N_BOOT} successful
"""

with open(os.path.join(OUT_LOGS, 'scheme_B_run.md'), 'w', encoding='utf-8') as f:
    f.write(run_log)
print("  scheme_B_run.md saved.")
print("\nAll done.")
