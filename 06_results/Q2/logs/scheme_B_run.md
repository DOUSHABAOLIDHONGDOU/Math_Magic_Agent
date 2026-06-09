# Q2 Scheme B Run Log (v2)

## Run Information
- Date: 2026-06-09
- Script: 05_code/Q2/q2_scheme_B.py
- Run command: `python3 05_code/Q2/q2_scheme_B.py` (from project root)
- Random seed: 42

## Q1-B v2 Parameters Inherited
- best_degree: 3
- n_knots: 5
- alpha: 88.58667904100822
- resid_std: 0.03151
- Source: 06_results/Q1/tables/scheme_B_metrics.csv

## Input Files
- 01_problem/source/CUMCM2025Problems/C题/附件.xlsx (sheet: 男胎检测数据)
- 05_code/Q1/q1_scheme_B.py (feature engineering reference)
- 06_results/Q1/tables/scheme_B_metrics.csv (confirmed Q1 model params)

## Data
- Cleaned rows: 1068
- Subjects: 267
- Y concentration (all obs): mean=0.0770, >=4%=86.4%

## Model-Predicted T_i*
- Censored (T_i*=26w): 0 (0.0%)
- T_i* range: 10.00 – 16.30 weeks
- T_i* == 10w: 263/267 (99%)
- Note: T_i* degeneracy – Q1 model predicts Y_hat >= 4% at week 10 for nearly all
  subjects. This reflects the high-BMI population studied (most BMI 28-40) where
  Y concentration is generally above 4% at the start of the clinical window.

## Empirical T_i* (from actual observations)
- Range: 11.00 – 24.71 weeks
- Median: 12.86 weeks
- Right-censored: 9 subjects (never observed Y >= 4%)
- Subjects with any Y<4% obs: 81 (30.3%)

## Key Results
- Best K: 3 (selected by min total risk, min_size=30)
- DP total risk (model T_i*): 1.000
- Empirical BMI grouping total risk: 1.000
- Risk reduction: 0.0%

## Grouping (K=3, model T_i*)
| Group | BMI Range | n | t* | t* (w+d) | T*_mean | Risk |
|-------|-----------|---|------|----------|---------|------|
| G1 | [20.7, 29.3] | 30 | 10.0w | 10w | 10.21w | 1.000 |
| G2 | [29.4, 30.0] | 30 | 10.0w | 10w | 10.00w | 0.000 |
| G3 | [30.1, 46.9] | 207 | 11.5w | 11w+4d | 10.02w | 0.000 |

## Empirical BMI Grouping
| Group | n | t* | t* (w+d) | T*_mean | Risk |
|-------|---|------|----------|---------|------|
| [20,28) | 4 | 10.0w | 10w | 11.57w | 1.000 |
| [28,32) | 138 | 10.0w | 10w | 10.00w | 0.000 |
| [32,36) | 98 | 10.0w | 10w | 10.00w | 0.000 |
| [36,40) | 22 | 11.5w | 11w+4d | 10.17w | 0.000 |
| [40,+∞) | 5 | 10.0w | 10w | 10.00w | 0.000 |

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
- Iterations: 100/100 successful
