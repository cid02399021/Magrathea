#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scientific archived data plotting."""
import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.family': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'figure.dpi': 100,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
    'figure.autolayout': False,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'lines.linewidth': 1.2,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
})

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = REPO_ROOT / 'experiments' / 'archive'
SUB = REPO_ROOT / 'experiments' / 'subneptune-20261027' / 'outputs'
PRESCRIBED = REPO_ROOT / 'experiments' / 'prescribed-tp-20261028'
RECIPROCAL = REPO_ROOT / 'experiments' / 'prescribed-tp-reciprocal-20261030'
HUANG = REPO_ROOT / 'experiments' / 'huang2022-fig4' / 'results' / 'results.json'

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def rel_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()

def read_json(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_csv(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_plot(fig, outdir: Path, stem: str):
    if fig.texts:
        fig.set_constrained_layout(True)
        fig.get_layout_engine().set(rect=(0, 0.10, 1, 0.90))
        for txt in fig.texts:
            txt.set_position((0.5, 0.018))
            txt.set_fontsize(10)
            txt.set_ha('center')
            txt.set_va('bottom')
            txt.set_wrap(True)
            new_text = '\n'.join(txt.get_text().splitlines()[:2])
            txt.set_text(new_text)
    else:
        fig.set_constrained_layout(True)
        fig.get_layout_engine().set(rect=(0, 0, 1, 1))

    fig.savefig(outdir / f'{stem}.png', dpi=200)
    fig.savefig(outdir / f'{stem}.svg')
    plt.close(fig)
def new_fig(nrows=1, ncols=1, figsize=(12, 5)):
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, constrained_layout=True)
    if nrows * ncols == 1:
        axes = np.array([axes])
    return fig, axes.flatten()

def safe_float(v, default=np.nan):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def add_source(sources: dict, path: Path):
    if not path.exists():
        raise FileNotFoundError(f'Missing source file: {path}')
    sources[rel_path(path)] = {'sha256': sha256_file(path), 'bytes': path.stat().st_size}

# ---------------------------------------------------------------------------
# Figure 1: baselines 20261018
# ---------------------------------------------------------------------------
def fig01(outdir: Path, sources: dict):
    cap_path = ARCHIVE / '20261018' / 'capstone' / 'summary.json'
    lit_path = ARCHIVE / '20261018' / 'literature-cases' / 'summary.json'
    huang_path = HUANG
    add_source(sources, cap_path)
    add_source(sources, lit_path)
    add_source(sources, huang_path)

    cap_data = read_json(cap_path)
    cap_runs = cap_data['runs']
    assert len(cap_runs) == 4
    huang_data = read_json(huang_path)
    huang_runs = huang_data['runs']
    assert len(huang_runs) == 4

    fig, axes = new_fig(2, 2, figsize=(12, 9))
    ax_a, ax_b, ax_c, ax_d = axes

    # Panel a: categorical radius bar for cold 300K and warm 1000K
    baseline = next(r for r in cap_runs if r['id'] == 'baseline_300K')
    warm = next(r for r in cap_runs if r['id'] == 'warm_1000K')
    ax_a.bar(['baseline_300K', 'warm_1000K'], [baseline['radius_RE'], warm['radius_RE']],
             color=['#24649a', '#bc4b51'])
    ax_a.set_ylabel('半径 [R$_E$]')
    ax_a.set_title('(a) 基础实践冷热运行半径')

    # Panel b: tighter radius deltas vs baseline in km
    earth_radius_cm = 637810000.0
    baseline_re = baseline['radius_RE']
    tighter_ids = ['baseline_300K', 'ode_tighter', 'ode_and_fit_tighter']
    tighter_rows = [r for r in cap_runs if r['id'] in tighter_ids]
    deltas = [(r['radius_RE'] - baseline_re) * earth_radius_cm / 100000.0 for r in tighter_rows]  # km
    ax_b.bar(range(len(tighter_rows)), deltas, tick_label=[r['id'] for r in tighter_rows],
             color=['#24649a', '#30917e', '#bc4b51'])
    ax_b.set_ylabel('半径变化 [km]')
    ax_b.set_title('(b) 收紧运行半径差')

    # Panel c: Huang paper three runs difference from printed precision
    paper_fixed = 0.9668
    paper_precision = 0.00005
    # exclude current default control and keep three smallest absolute diff
    huang_sorted = sorted([r for r in huang_runs if r['id'] != 'current_default_control'],
                          key=lambda r: abs(r['radius_RE'] - paper_fixed))
    selected_huang = huang_sorted[:3]
    excluded = [r for r in huang_runs if r not in selected_huang]
    diffs = [(r['radius_RE'] - paper_fixed) * 1e5 for r in selected_huang]
    labels = [r['id'] for r in selected_huang]
    ax_c.scatter(labels, diffs, color='#24649a', s=40)
    for i, diff in enumerate(diffs):
        ax_c.annotate(f'{diff:.2f}', (labels[i], diffs[i]), textcoords='offset points', xytext=(5, 5), fontsize=9)
    ax_c.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax_c.axhspan(-paper_precision * 1e5, paper_precision * 1e5, color='#f0a', alpha=0.2,
                 label='打印精度 ±5 单位')
    ax_c.set_xlabel('运行 ID')
    ax_c.set_ylabel('半径差 [10^-5 R⊕]')
    ax_c.set_title('(c) Huang 论文运行半径差')
    ax_c.legend()

    # Panel d: all four Huang radii including default mantle, target
    huang_all = huang_runs
    ax_d.bar([r['id'] for r in huang_all], [r['radius_RE'] for r in huang_all],
             color='#30917e')
    ax_d.set_ylabel('半径 [R$_E$]')
    ax_d.set_title('(d) 所有 Huang 运行半径')
    plt.setp(ax_d.get_xticklabels(), rotation=45, ha='right')

    save_plot(fig, outdir, '01-baselines-20261018')
    return {
        'capstone_runs': cap_runs,
        'huang_runs': huang_runs,
        'excluded_huang_id': excluded[0]['id'] if excluded else None,
        'capstone_core_fraction': cap_data.get('core_fraction', 0.325),
        'huang_core_fraction': huang_data.get('core_fraction', 0.33),
        'plotted_values': {
            'capstone_baseline_radius': baseline['radius_RE'],
            'huang_paper_fixed': paper_fixed,
            'huang_precision': paper_precision
        }
    }

# ---------------------------------------------------------------------------
# Figure 2: recipes 20261018
# ---------------------------------------------------------------------------
def fig02(outdir: Path, sources: dict):
    lit_path = ARCHIVE / '20261018' / 'literature-cases' / 'summary.json'
    add_source(sources, lit_path)
    data = read_json(lit_path)
    display_cases = data['display_cases']
    runs = data['runs']

    cases = []
    for dc in display_cases:
        case_id = dc['id']
        run = None
        for r in runs:
            if r['id'] == case_id:
                run = r
                break
        if run is None:
            raise ValueError(f'Missing run for case {case_id}')
        cases.append({'display': dc, 'run': run})
    assert len(cases) == 6

    fig, axes = new_fig(1, 2, figsize=(12, 6))
    ax1, ax2 = axes
    labels = [c['display']['label'] for c in cases]
    radii = [c['run']['radius_RE'] for c in cases]
    fractions = [c['run']['fractions_Fe_Si_water_gas'] for c in cases]
    rock_frac = [f[0] + f[1] for f in fractions]
    water_frac = [f[2] for f in fractions]
    gas_frac = [f[3] for f in fractions]

    # assert fraction sums
    for i, f in enumerate(fractions):
        s = sum(f)
        assert abs(s - 1.0) < 1e-9, f'Case {labels[i]} fraction sum {s} != 1'

    x = np.arange(len(cases))
    width = 0.35
    ax1.bar(x, rock_frac, width, label='岩石 (Fe+Si)', color='#24649a')
    ax1.bar(x, water_frac, width, bottom=rock_frac, label='水', color='#30917e')
    ax1.bar(x, gas_frac, width, bottom=np.array(rock_frac)+np.array(water_frac), label='气体', color='#bc4b51')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.set_ylabel('质量分数')
    ax1.set_title('(a) 质量分数 (岩石/水/气体)')
    ax1.legend()

    # annotate tiny positive gas as percent
    for i, gf in enumerate(gas_frac):
        if gf > 0:
            pct = gf * 100
            ax1.annotate(f'{pct:.3g}%', (i, rock_frac[i]+water_frac[i]+gf), xytext=(0, 5),
                         textcoords='offset points', fontsize=9, ha='center')

    ax2.bar(x, radii, color='#24649a')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45, ha='right')
    ax2.set_ylabel('半径 [R_E]')
    ax2.set_title('(b) 半径')

    fig.text(0.5, 0.01, '注：总质量为7.1/8.04 M⊕，边界/EOS不同；配方不代表纯成分推断。',
             ha='center', fontsize=9)

    save_plot(fig, outdir, '02-recipes-20261018')
    return {
        'cases': cases,
        'plotted_values': {
            'labels': labels,
            'radii': radii,
            'rock_frac': rock_frac,
            'water_frac': water_frac,
            'gas_frac': gas_frac,
            'selected_ids': [c['display']['id'] for c in cases],
            'raw_fractions': fractions
        }
    }
# ---------------------------------------------------------------------------
# Figure 3: grey 20261025
# ---------------------------------------------------------------------------
def fig03(outdir: Path, sources: dict):
    base = SUB / 'tp-comparison-20261025-dedb3d'
    profiles_path = base / 'profiles.csv'
    comparison_path = base / 'comparison.csv'
    add_source(sources, profiles_path)
    add_source(sources, comparison_path)
    profiles = read_csv(profiles_path)
    comparison = read_csv(comparison_path)

    rows_profiles = []
    for row in profiles:
        try:
            p = float(row['pressure_bar'])
            ref = float(row['reference_K'])
            j1 = float(row['adiabat_1bar_K'])
            j10 = float(row['adiabat_10bar_K'])
            j100 = float(row['adiabat_100bar_K'])
            if p > 0 and np.isfinite(p) and np.isfinite(ref) and np.isfinite(j1) and np.isfinite(j10) and np.isfinite(j100):
                rows_profiles.append((p, ref, j1, j10, j100))
        except (ValueError, KeyError):
            pass
    assert len(rows_profiles) == 61, f'Expected 61 profiles rows, got {len(rows_profiles)}'
    rows_profiles.sort(key=lambda r: r[0])
    p_arr = np.array([r[0] for r in rows_profiles])
    ref_arr = np.array([r[1] for r in rows_profiles])
    j1_arr = np.array([r[2] for r in rows_profiles])
    j10_arr = np.array([r[3] for r in rows_profiles])
    j100_arr = np.array([r[4] for r in rows_profiles])

    comp_rows = []
    for row in comparison:
        try:
            comp_rows.append({
                'Tint': float(row['tint_K']),
                'gamma': float(row['gamma']),
                'anchor': float(row['anchor_bar']),
                'bottom_delta': float(row['bottom_delta_percent']),
                'nlevel': int(float(row['nlevel']))
            })
        except (ValueError, KeyError):
            pass
    # filter nlevel == 721
    comp_filtered = [r for r in comp_rows if r['nlevel'] == 721]
    assert len(comp_filtered) == 18, f'Expected 18 comparison rows, got {len(comp_filtered)}'

    fig, axes = new_fig(1, 2, figsize=(12, 5.5))
    ax1, ax2 = axes

    ax1.plot(ref_arr, p_arr, label='reference', color='black')
    ax1.plot(j1_arr, p_arr, label='join 1 bar', color='#24649a', linestyle='--')
    ax1.plot(j10_arr, p_arr, label='join 10 bar', color='#30917e', linestyle='--')
    ax1.plot(j100_arr, p_arr, label='join 100 bar', color='#bc4b51', linestyle='--')
    ax1.set_yscale('log')
    ax1.invert_yaxis()
    ax1.set_xlabel('温度 [K]')
    ax1.set_ylabel('压力 [bar]')
    ax1.set_title('(a) T-P 剖面（Teq=350K, Tint=25K, γ=0.1）')
    ax1.legend()

    pairs = {}
    for r in comp_filtered:
        key = (r['Tint'], r['gamma'])
        pairs.setdefault(key, []).append((r['anchor'], r['bottom_delta']))
    colors = ['#24649a', '#bc4b51', '#30917e']
    for idx, ((tint, gamma), points) in enumerate(sorted(pairs.items())):
        points.sort(key=lambda x: x[0])
        anchors = [p[0] for p in points]
        deltas = [p[1] for p in points]
        ax2.plot(anchors, deltas, marker='o', linestyle='-', color=colors[idx % 3],
                 label=f'Tint={tint}, γ={gamma}')
    ax2.set_xscale('log')
    ax2.set_xlabel('连接压力 [bar]')
    ax2.set_ylabel('底部温度相对辐射参考差 [%]')
    ax2.set_title('(b) 底部温度差 vs 连接压力')
    ax2.legend()
    fig.text(0.5, 0.01, '人工接点并非RCB、无完整行星半径。直线仅为引导。', ha='center', fontsize=9)

    save_plot(fig, outdir, '03-grey-20261025')
    return {
        'profiles_rows': len(rows_profiles),
        'comparison_rows': len(comp_filtered),
        'plotted_values': {
            'P': p_arr.tolist(),
            'reference': ref_arr.tolist(),
            'j1': j1_arr.tolist(),
            'j10': j10_arr.tolist(),
            'j100': j100_arr.tolist(),
            'anchors': {f'{tint}_{gamma}': [p[0] for p in points] for (tint,gamma), points in pairs.items()},
            'deltas': {f'{tint}_{gamma}': [p[1] for p in points] for (tint,gamma), points in pairs.items()}
        }
    }

# ---------------------------------------------------------------------------
# Figure 4: boundary 20261025
# ---------------------------------------------------------------------------
def fig04(outdir: Path, sources: dict):
    path = SUB / 'mode0-inputs-20261025-a17b' / 'comparison.csv'
    add_source(sources, path)
    rows = read_csv(path)
    target_ids = ['demo5_T300', 'demo5_T360', 'demo5_T450', 'demo8p04_T300', 'demo8p04_T360', 'demo8p04_T450']
    selected = []
    for row in rows:
        if row['case_id'] in target_ids:
            selected.append(row)
    assert len(selected) == 6, f'Expected 6 rows, got {len(selected)}'

    for r in selected:
        r['radius_re'] = float(r['radius_re'])
        r['surface_temperature_K'] = float(r['surface_temperature_K'])
        r['mass_me'] = float(r['mass_me'])
        assert np.isfinite(r['radius_re']) and np.isfinite(r['surface_temperature_K']) and np.isfinite(r['mass_me'])

    selected.sort(key=lambda r: (r['mass_me'], r['surface_temperature_K']))
    fig, axes = new_fig(1, 2, figsize=(12, 5))
    ax1, ax2 = axes

    colors = {5.0: '#24649a', 8.04: '#bc4b51'}
    for m in [5.0, 8.04]:
        subset = [r for r in selected if abs(r['mass_me'] - m) < 1e-6]
        temps = [r['surface_temperature_K'] for r in subset]
        rads = [r['radius_re'] for r in subset]
        ax1.plot(temps, rads, marker='o', linestyle='-', color=colors[m], label=f'质量 {m} M$_E$')
        for t, rad, r in zip(temps, rads, subset):
            ax1.annotate(r['case_id'], (t, rad), textcoords='offset points', xytext=(5, 5), fontsize=9)
    ax1.set_xlabel('边界温度 [K]')
    ax1.set_ylabel('半径 [R$_E$]')
    ax1.set_title('(a) 半径 vs 边界温度')
    ax1.legend()

    # percent relative change from 300K
    for m in [5.0, 8.04]:
        subset = [r for r in selected if abs(r['mass_me'] - m) < 1e-6]
        base = next(r['radius_re'] for r in subset if abs(r['surface_temperature_K'] - 300.0) < 1e-6)
        temps = [r['surface_temperature_K'] for r in subset]
        pct = [(r['radius_re'] - base) / base * 100 for r in subset]
        ax2.plot(temps, pct, marker='o', linestyle='-', color=colors[m], label=f'质量 {m} M$_E$')
    ax2.set_xlabel('边界温度 [K]')
    ax2.set_ylabel('半径相对变化 [%]')
    ax2.set_title('(b) 半径相对变化（固定1%气体、0.05bar）')
    ax2.legend()

    save_plot(fig, outdir, '04-boundary-20261025')
    return {
        'selected': selected,
        'plotted_values': {
            'case_ids': [r['case_id'] for r in selected],
            'mass': [r['mass_me'] for r in selected],
            'temp': [r['surface_temperature_K'] for r in selected],
            'radius': [r['radius_re'] for r in selected]
        }
    }

# ---------------------------------------------------------------------------
# Figure 5: thermal-composition 20261025
# ---------------------------------------------------------------------------
def fig05(outdir: Path, sources: dict):
    base = SUB / 'thermal-composition-20261025-b01'
    forward_path = base / 'forward.csv'
    recovery_path = base / 'recovery.csv'
    add_source(sources, forward_path)
    add_source(sources, recovery_path)
    forward = read_csv(forward_path)
    recovery = read_csv(recovery_path)
    assert len(forward) == 18, f'Expected 18 forward rows, got {len(forward)}'
    assert len(recovery) == 4, f'Expected 4 recovery rows, got {len(recovery)}'

    for r in forward:
        r['mass_me'] = float(r['mass_me'])
        r['temperature_K'] = float(r['temperature_K'])
        r['fraction'] = float(r['fraction'])
        r['radius_re'] = float(r['radius_re'])
    for r in recovery:
        r['mass_me'] = float(r['mass_me'])
        r['assumed_temperature_K'] = float(r['assumed_temperature_K'])
        r['recovered_fraction'] = float(r['recovered_fraction'])

    masses = sorted(set(r['mass_me'] for r in forward))
    fig, axes = new_fig(1, 3, figsize=(16, 5))
    ax1, ax2, ax3 = axes

    colors_t = ['#24649a', '#bc4b51', '#30917e']
    for idx, m in enumerate(masses):
        ax = axes[idx]
        subset = [r for r in forward if r['mass_me'] == m]
        temps = sorted(set(r['temperature_K'] for r in subset))
        for t, c in zip(temps, colors_t):
            rows_t = sorted([r for r in subset if r['temperature_K'] == t], key=lambda r: r['fraction'])
            ax.plot([r['fraction'] * 100 for r in rows_t], [r['radius_re'] for r in rows_t],
                    marker='o', linestyle='-', color=c, label=f'T={t:.0f}K')
        ax.set_xlabel('气体质量分数 [%]')
        ax.set_ylabel('半径 [R$_E$]')
        ax.set_title(f'{"(a)" if idx==0 else "(b)"} 质量 {m:.2f} M$_E$')
        ax.legend()

    # recovery points
    colors_m = {5.0: '#24649a', 8.04: '#bc4b51'}
    # collect unique recovery labels per mass
    recovery_labels = {}
    for r in recovery:
        m = r['mass_me']
        if m not in recovery_labels:
            recovery_labels[m] = f"M={m:.2f} M$_E$"

    for r in recovery:
        ax3.scatter(r['assumed_temperature_K'], r['recovered_fraction'] * 100,
                    color=colors_m.get(r['mass_me'], 'gray'), s=50,
                    label=recovery_labels.get(r['mass_me'], f"M={r['mass_me']:.2f} M$_E$"))

        # Use different offsets for 300K vs 450K to avoid overlap
        if r['assumed_temperature_K'] < 400:
            xytext = (5, 10)
            ha = 'left'
        else:
            xytext = (-5, -10)
            ha = 'right'
        # Instead of annotating value at point, we'll create small text boxes in lower right of ax3 for values that overlap
        # We'll store values for later text box
    # Add text box with numeric values for recoveries that may overlap (e.g., around 0.38/0.39)
    # We'll place a small text box in lower right of ax3 with all recovery fractions
    recovery_text_lines = []
    for r in recovery:
        recovery_text_lines.append(f"{r['assumed_temperature_K']:.0f}K: {r['recovered_fraction']*100:.2f}%")
    recovery_text = '\n'.join(recovery_text_lines)
    ax3.text(0.98, 0.02, recovery_text, transform=ax3.transAxes, fontsize=8,
             ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    # truth point 360K 1%
    truth = next(r for r in forward if abs(r['temperature_K'] - 360.0) < 1e-9 and abs(r['fraction'] - 0.01) < 1e-9)
    ax3.scatter(360.0, 1.0, marker='*', s=150, color='black', label='真值 360K 1%')
    ax3.set_xlabel('假设温度 [K]')
    ax3.set_ylabel('恢复气体分数 [%]')
    ax3.set_title('(c) 恢复气体分数')
    ax3.legend()
    fig.text(0.5, 0.01, '恢复值是合成点估计，不是后验；改变表面温度。直线仅作引导。', ha='center', fontsize=10)

    save_plot(fig, outdir, '05-thermal-composition-20261025')
    return {
        'forward_rows': len(forward),
        'recovery_rows': len(recovery),
        'plotted_values': {
            'forward': {'mass': [r['mass_me'] for r in forward], 'temp': [r['temperature_K'] for r in forward],
                        'frac': [r['fraction'] for r in forward], 'radius': [r['radius_re'] for r in forward]},
            'recovery': {'mass': [r['mass_me'] for r in recovery], 'temp': [r['assumed_temperature_K'] for r in recovery],
                         'frac': [r['recovered_fraction'] for r in recovery]}
        }
    }
# ---------------------------------------------------------------------------
# Figure 6: prescribed forward 20261029
# ---------------------------------------------------------------------------
def fig06(outdir: Path, sources: dict):
    summary_path = PRESCRIBED / 'summary.json'
    a_profile_path = PRESCRIBED / 'data' / 'A-truth' / 'profile.csv'
    b_profile_path = PRESCRIBED / 'data' / 'B-truth' / 'profile.csv'
    for p in [summary_path, a_profile_path, b_profile_path]:
        add_source(sources, p)
    summary = read_json(summary_path)
    a_profile = read_csv(a_profile_path)
    b_profile = read_csv(b_profile_path)
    assert len(a_profile) >= 2, 'A-truth profile must have >=2 rows'
    assert len(b_profile) >= 2, 'B-truth profile must have >=2 rows'

    # parse profile rows
    def parse_profile(rows):
        out = []
        for r in rows:
            p = safe_float(r.get('P_bar', r.get('pressure_bar')))
            t = safe_float(r.get('T_K', r.get('temperature_K')))
            if np.isfinite(p) and np.isfinite(t) and p > 0:
                out.append((p, t))
        assert len(out) >= 2
        return out

    a_prof = parse_profile(a_profile)
    b_prof = parse_profile(b_profile)

    fig, axes = new_fig(1, 2, figsize=(12, 5.5))
    ax1, ax2 = axes

    ax1.plot([t for p, t in a_prof], [p for p, t in a_prof], marker='o', markersize=4, label='A-truth', color='#24649a')
    ax1.plot([t for p, t in b_prof], [p for p, t in b_prof], marker='s', markersize=4, label='B-truth', color='#bc4b51')
    ax1.set_yscale('log')
    ax1.invert_yaxis()
    ax1.set_xlabel('温度 [K]')
    ax1.set_ylabel('压力 [bar]')
    ax1.set_title('输入廓线覆盖表 (不是实际气层深度)')
    ax1.legend()

    # relative signals bars from summary
    signals = ['thermal_signal_relative_to_A', 'tight_relative_to_B', 'collinear_refine_relative_to_A']
    vals = [abs(summary[s]) for s in signals]
    labels = ['TP形状差异', '收紧容差', '共线节点细化']
    colors = ['#24649a', '#30917e', '#bc4b51']
    ax2.bar(labels, vals, color=colors)
    ax2.set_yscale('log')
    ax2.set_ylabel('相对信号绝对值 (无量纲)')
    ax2.set_title('(b) 相对信号大小')
    for i, v in enumerate(vals):
        ax2.text(i, v, f'{v:.2e}', ha='center', va='bottom', fontsize=9)

    # Add thermal_signal_km annotation if available
    if summary.get('thermal_signal_km') is not None:
        fig.text(0.5, 0.02, f'thermal_signal_km: {summary["thermal_signal_km"]}', ha='center', fontsize=9)

    save_plot(fig, outdir, '06-prescribed-forward-20261029')
    return {
        'summary': summary,
        'plotted_values': {
            'A_P': [p for p, t in a_prof],
            'A_T': [t for p, t in a_prof],
            'B_P': [p for p, t in b_prof],
            'B_T': [t for p, t in b_prof],
            'signal_relative': {s: abs(summary[s]) for s in signals},
            'thermal_signal_km': summary.get('thermal_signal_km')
        }
    }
# ---------------------------------------------------------------------------
# Figure 7: original failure 20261029
# ---------------------------------------------------------------------------
def fig07(outdir: Path, sources: dict):
    summary_path = PRESCRIBED / 'summary.json'
    add_source(sources, summary_path)
    summary = read_json(summary_path)
    cases = summary['cases']
    target_names = ['A-recovery-low', 'A-truth', 'A-recovery-high', 'B-truth']
    selected = [c for c in cases if c['name'] in target_names]
    assert len(selected) == 4, f'Expected 4 cases, got {len(selected)}'

    for c in selected:
        c['gas_fraction'] = float(c['gas_fraction'])
        c['radius_earth'] = float(c['radius_earth'])
        c['rounded_boundary']['radius_earth'] = float(c['rounded_boundary']['radius_earth'])
        c['rounded_boundary']['gas_thickness_earth'] = float(c['rounded_boundary']['gas_thickness_earth'])
        c['rounded_boundary']['solid_density'] = float(c['rounded_boundary']['solid_density'])
        if 'gas_base_density' in c:
            c['gas_base_density'] = float(c['gas_base_density'])

    fig, axes = new_fig(1, 2, figsize=(12, 5.5))
    ax1, ax2 = axes

    # left: gas fraction vs radius for A cases, B-truth as horizontal target
    a_cases = [c for c in selected if c['name'] != 'B-truth']
    b_truth = next(c for c in selected if c['name'] == 'B-truth')
    # sort A cases by gas fraction
    a_cases.sort(key=lambda c: c['gas_fraction'])
    fgs = [c['gas_fraction'] for c in a_cases]
    rads = [c['radius_earth'] for c in a_cases]
    ax1.plot(fgs, rads, marker='o', linestyle='-', color='#24649a')
    # Annotate names, moving labels inward to avoid clipped right edge
    for fg, rad, c in zip(fgs, rads, a_cases):
        # If near right edge, move label left and up
        if fg > 0.15:
            xytext = (-10, 10)
            ha = 'right'
        else:
            xytext = (5, 5)
            ha = 'left'
        ax1.annotate(c['name'], (fg, rad), textcoords='offset points', xytext=xytext, ha=ha, fontsize=9)
    ax1.axhline(b_truth['radius_earth'], color='#bc4b51', linestyle='--', label=f'B-truth {b_truth["radius_earth"]:.6f}')
    ax1.set_xscale('log')
    ax1.set_xlabel('气体质量分数 [对数刻度]')
    ax1.set_ylabel('半径 [R_E]')
    ax1.set_title('(a) 实际气体分数 vs 半径 (失败端点)')
    ax1.legend()

    # right: one stacked bar per A case at same x numeric positions
    solid_list = [c['rounded_boundary']['radius_earth'] for c in a_cases]
    thick_list = [c['rounded_boundary']['gas_thickness_earth'] for c in a_cases]
    total_list = [s + t for s, t in zip(solid_list, thick_list)]
    for i, (s, t, tot, c) in enumerate(zip(solid_list, thick_list, total_list, a_cases)):
        assert abs(tot - c['radius_earth']) <= 1e-7, f'Sum mismatch for {c["name"]}: {tot} vs {c["radius_earth"]}'
    xpos = np.arange(len(a_cases))
    ax2.bar(xpos, solid_list, color='#24649a', label='固体半径')
    ax2.bar(xpos, thick_list, bottom=solid_list, color='#bc4b51', label='气体厚度')
    ax2.set_xticks(xpos)
    ax2.set_xticklabels([c['name'] for c in a_cases])
    ax2.set_ylabel('半径 [R_E]')
    ax2.set_title('(b) 半径组成（A 案例）')
    ax2.legend()
    high = a_cases[-1]  # highest gas fraction
    # Combine density text into two lines in a box at axes-relative position
    density_text = ""
    if 'gas_base_density' in high:
        density_text += f'高气体案例气体底部密度 {high["gas_base_density"]:.4f} g/cm³\n'
    density_text += f'高气体案例固体密度 {high["rounded_boundary"]["solid_density"]:.4f} g/cm³'
    ax2.text(0.02, 0.02, density_text, transform=ax2.transAxes, fontsize=10,
             va='bottom', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    fig.text(0.5, 0.01, '端点失败不排除内部根；气体密度14.53 vs 4.71适用性存疑，非不稳定性证明。', ha='center', fontsize=9)

    save_plot(fig, outdir, '07-original-failure-20261029')
    return {
        'selected': selected,
        'plotted_values': {
            'fg': fgs,
            'radius': rads,
            'b_truth_radius': b_truth['radius_earth'],
            'solid_radius': solid_list,
            'gas_thickness': thick_list,
            'gas_base_density': high.get('gas_base_density'),
            'solid_density': high['rounded_boundary']['solid_density']
        }
    }
# ---------------------------------------------------------------------------
# Figure 8: local recovery 20261030
# ---------------------------------------------------------------------------
def fig08(outdir: Path, sources: dict):
    summary_path = RECIPROCAL / 'summary.json'
    old_summary_path = PRESCRIBED / 'summary.json'
    add_source(sources, summary_path)
    add_source(sources, old_summary_path)
    summary = read_json(summary_path)
    old_summary = read_json(old_summary_path)

    records = summary['records']
    search_records = [r for r in records if r['kind'] == 'search']
    confirmation_records = [r for r in records if r['kind'] == 'confirmation']
    assert len(search_records) == 4, f'Expected 4 search records, got {len(search_records)}'
    assert len(confirmation_records) == 2, f'Expected 2 confirmation records, got {len(confirmation_records)}'

    # Do not mutate original records; create new lists for plotting
    fgs = [float(r['gas_fraction']) * 100 for r in search_records]  # percent
    residuals = [float(r['target_relative_residual']) * 100 for r in search_records]  # percent

    fig, axes = new_fig(1, 3, figsize=(16, 5))
    ax1, ax2, ax3 = axes

    # Panel 1: scatter of search records with log x, remove individual annotations, add legend entry
    ax1.scatter(fgs, residuals, color='#24649a', s=60, label='4次搜索')
    ax1.axhline(0, color='gray', linestyle='--')
    ax1.set_xscale('log')

    # old B-truth endpoint
    old_cases = old_summary['cases']
    a_truth_old = next(c for c in old_cases if c['name'] == 'A-truth')
    b_truth_old = next(c for c in old_cases if c['name'] == 'B-truth')
    old_residual_pct = (float(b_truth_old['radius_earth']) - float(a_truth_old['radius_earth'])) / float(a_truth_old['radius_earth']) * 100
    ax1.scatter([1.0], [old_residual_pct], marker='s', s=100, color='#bc4b51', label='旧 B-truth 端点 1%')

    # inferred root
    inferred_pct = float(summary['recovery']['inferred_fraction']) * 100
    nominal_residual_pct = float(summary['recovery']['nominal_radius_relative_residual']) * 100
    ax1.scatter([inferred_pct], [nominal_residual_pct], marker='*', s=150, color='#30917e', label='推断局部根')
    ax1.set_xlabel('气体质量分数 [%] (对数)')
    ax1.set_ylabel('半径残差 [%]')
    ax1.set_title('(a) 搜索记录：气体分数 vs 半径残差')
    ax1.legend()

    # Panel 2: true vs inferred bar, move bias annotation into axes
    true_pct = float(summary['truth']['gas_fraction']) * 100
    bias_pct = float(summary['recovery']['relative_bias']) * 100
    ax2.bar(['真值'], [true_pct], color='#24649a', label='真值')
    ax2.bar(['推断'], [inferred_pct], color='#bc4b51', label='推断')
    ax2.set_ylabel('气体质量分数 [%]')
    ax2.set_title('(b) 真值 vs 推断')
    ax2.legend()
    # Position bias text at 90% height, centered within axes
    ax2.text(0.5, 0.9, f'相对偏差 {bias_pct:.2f}%', transform=ax2.transAxes,
             ha='center', va='center', fontsize=9)

    # Panel 3: absolute residual log bars (dimensionless, not percent)
    nominal_abs = abs(float(summary['recovery']['nominal_radius_relative_residual']))
    conf_abs = [abs(float(c['target_relative_residual'])) for c in confirmation_records]
    assert all(v < 1e-5 for v in [nominal_abs] + conf_abs), 'Confirmation residual >= 1e-5'
    values = [nominal_abs] + conf_abs
    labels = ['nominal'] + [c['case'] for c in confirmation_records]
    ax3.bar(labels, values, color=['#24649a', '#30917e', '#bc4b51'])
    ax3.set_yscale('log')
    ax3.axhline(5e-6, color='orange', linestyle='--', label='阈值 5e-6 (名义)')
    ax3.axhline(1e-5, color='purple', linestyle='--', label='阈值 1e-5 (确认)')
    ax3.set_ylabel('绝对半径相对残差 (无量纲, log)')
    ax3.set_title('(c) 名义与确认绝对残差')
    ax3.legend()
    for i, v in enumerate(values):
        ax3.text(i, v, f'{v:.2e}', ha='center', va='bottom', fontsize=9)

    # Footer text with bracket info if available, but change wording per instruction
    bracket = summary['recovery'].get('signed_bracket_fraction')
    if bracket:
        footer_text = f'原失败后选择A→B，未证明唯一；数值括区间不是置信区间 [{bracket[0]:.3e}, {bracket[1]:.3e}]。'
    else:
        footer_text = '原失败后选择A→B，未证明唯一；数值括区间不是置信区间。'
    fig.text(0.5, 0.01, footer_text, ha='center', fontsize=9)

    save_plot(fig, outdir, '08-local-recovery-20261030')
    return {
        'summary': summary,
        'plotted_values': {
            'search_fg': fgs,
            'search_residual': residuals,
            'old_B_truth_residual': old_residual_pct,
            'true_pct': true_pct,
            'inferred_pct': inferred_pct,
            'bias_pct': bias_pct,
            'nominal_abs': nominal_abs,
            'conf_abs': conf_abs
        }
    }
# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    outdir = Path(args.output_dir)
    if outdir.exists():
        print(f'Error: output directory {outdir} already exists.', file=sys.stderr)
        sys.exit(1)
    outdir.mkdir(parents=True)

    sources = {}
    metadata = {
        'generated_by': 'plot_history.py',
        'repo_root': str(REPO_ROOT),
        'date': '20261102',
        'figures': []
    }

    results = {}
    results['fig01'] = fig01(outdir, sources)
    results['fig02'] = fig02(outdir, sources)
    results['fig03'] = fig03(outdir, sources)
    results['fig04'] = fig04(outdir, sources)
    results['fig05'] = fig05(outdir, sources)
    results['fig06'] = fig06(outdir, sources)
    results['fig07'] = fig07(outdir, sources)
    results['fig08'] = fig08(outdir, sources)

    captions = {
        '01-baselines-20261018': {
            'caption_zh': '基础实践运行与黄论文运行基线对比。',
            'takeaway_zh': '默认半径差异大；论文打印精度仅 ±5e-5。'
        },
        '02-recipes-20261018': {
            'caption_zh': '六种文献案例的质量分数与半径。',
            'takeaway_zh': '不同 EOS/边界，配方不构成观测推断。'
        },
        '03-grey-20261025': {
            'caption_zh': '灰大气 T-P 剖面与人工连接点比较。',
            'takeaway_zh': '连接压力为人为预设，非真实 RCB。'
        },
        '04-boundary-20261025': {
            'caption_zh': '边界温度敏感性：固定1%气体、0.05bar。',
            'takeaway_zh': '边界温度显著改变半径，但不代表固定边界形状。'
        },
        '05-thermal-composition-20261025': {
            'caption_zh': '热成分前向模型与恢复测试。',
            'takeaway_zh': '恢复偏差为合成点估计，非置信区间。'
        },
        '06-prescribed-forward-20261029': {
            'caption_zh': '预设 T-P 剖面前向比较。',
            'takeaway_zh': '共线细化不是任意曲线验证。'
        },
        '07-original-failure-20261029': {
            'caption_zh': '原始恢复失败：端点未包围。',
            'takeaway_zh': '端点失败不排除内部根；气体密度适用性存疑。'
        },
        '08-local-recovery-20261030': {
            'caption_zh': '反方向局部恢复。',
            'takeaway_zh': '推断局部根数值存在，但原始方向仍失败，无全局唯一性证明。'
        }
    }

    source_paths_by_stem = {
        '01-baselines-20261018': [
            'experiments/archive/20261018/capstone/summary.json',
            'experiments/huang2022-fig4/results/results.json'
        ],
        '02-recipes-20261018': [
            'experiments/archive/20261018/literature-cases/summary.json'
        ],
        '03-grey-20261025': [
            'experiments/subneptune-20261027/outputs/tp-comparison-20261025-dedb3d/profiles.csv',
            'experiments/subneptune-20261027/outputs/tp-comparison-20261025-dedb3d/comparison.csv'
        ],
        '04-boundary-20261025': [
            'experiments/subneptune-20261027/outputs/mode0-inputs-20261025-a17b/comparison.csv'
        ],
        '05-thermal-composition-20261025': [
            'experiments/subneptune-20261027/outputs/thermal-composition-20261025-b01/forward.csv',
            'experiments/subneptune-20261027/outputs/thermal-composition-20261025-b01/recovery.csv'
        ],
        '06-prescribed-forward-20261029': [
            'experiments/prescribed-tp-20261028/summary.json',
            'experiments/prescribed-tp-20261028/data/A-truth/profile.csv',
            'experiments/prescribed-tp-20261028/data/B-truth/profile.csv'
        ],
        '07-original-failure-20261029': [
            'experiments/prescribed-tp-20261028/summary.json'
        ],
        '08-local-recovery-20261030': [
            'experiments/prescribed-tp-reciprocal-20261030/summary.json',
            'experiments/prescribed-tp-20261028/summary.json'
        ]
    }

    for stem in ['01-baselines-20261018', '02-recipes-20261018', '03-grey-20261025',
                 '04-boundary-20261025', '05-thermal-composition-20261025',
                 '06-prescribed-forward-20261029', '07-original-failure-20261029',
                 '08-local-recovery-20261030']:
        metadata['figures'].append({
            'stem': stem,
            'filenames': [f'{stem}.png', f'{stem}.svg'],
            'caption_zh': captions[stem]['caption_zh'],
            'takeaway_zh': captions[stem]['takeaway_zh'],
            'source_paths': source_paths_by_stem[stem],
            'date': stem.split('-')[-1]
        })
    assert len(metadata['figures']) == 8
    for fig in metadata['figures']:
        for fname in fig['filenames']:
            assert (outdir / fname).exists(), f'Missing {fname}'
    metadata.pop('repo_root', None)
    metadata['engineering_milestones'] = '10-27 workflow; 10-28 interface.'
    plotted_values = {}
    for fig_key, res in results.items():
        if 'plotted_values' in res:
            plotted_values[fig_key] = res['plotted_values']

    metadata['sources'] = sources
    with open(outdir / 'plots.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    with open(outdir / 'plotted-values.json', 'w', encoding='utf-8') as f:
        json.dump(plotted_values, f, indent=2)

    print(f'Successfully generated 8 figures and metadata in {outdir}')

if __name__ == '__main__':
    main()
