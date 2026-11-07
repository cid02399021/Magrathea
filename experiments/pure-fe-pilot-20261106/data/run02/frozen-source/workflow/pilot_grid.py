import math


def make_grid(u_values, gas_values):
    """Build grid of compositions for given u and gas fraction values.

    u: mass fraction of Fe in solid core, i.e., Fe / (Fe + water) (0..1)
    gas: total gas mass fraction (0..1)
    Returns list of dicts with keys: u, gas_fraction, fractions [Fe, mantle, water, gas]
    """
    if not u_values or not gas_values:
        raise ValueError("empty lists")
    if len(u_values) != len(set(u_values)) or len(gas_values) != len(set(gas_values)):
        raise ValueError("duplicate values")
    for v in u_values + gas_values:
        if not math.isfinite(v):
            raise ValueError("non-finite value")
    # Accept u=1 (all Fe), reject u=0 (no Fe)
    if any(u <= 0 or u > 1 for u in u_values):
        raise ValueError("u out of range")
    if any(g <= 0 or g >= 1 for g in gas_values):
        raise ValueError("gas fraction out of range")
    grid = []
    for g in gas_values:
        for u in u_values:
            fe = (1 - g) * u
            water = (1 - g) * (1 - u)
            grid.append({
                'u': u,
                'gas_fraction': g,
                'fractions': [fe, 0, water, g],
            })
    return grid


def crossings(rows, target):
    """Find crossings of radius_earth == target among input rows.

    rows: list of dicts with keys 'u', 'gas_fraction', 'status', 'radius_earth'
          (radius_earth may be None)
    target: target radius (positive finite)
    Returns list of crossing dicts:
        - DIRECT_SAMPLE: when a sample exactly matches target.
          Duplicates (same u and gas_fraction) are deduplicated.
          Includes fractions when direct sample has them.
        - INTERPOLATED_UNCONFIRMED: interpolation between adjacent gas fractions
          at same u suggests a crossing.
          Interpolation uses log(gas_fraction) with residual = radius - target linear.
          radius_earth is None for interpolated points.
          Includes fractions as [ (1-g)*u, 0, (1-g)*(1-u), g ] using interpolated g.
    """
    if target <= 0 or not math.isfinite(target):
        return []
    # group by u, skipping invalid u values (<=0 or >1)
    groups = {}
    for row in rows:
        u = row.get('u')
        if u is None or not math.isfinite(u) or u <= 0 or u > 1:
            continue
        groups.setdefault(u, []).append(row)
    results = []
    for u, group in groups.items():
        # sort by gas_fraction ascending
        group.sort(key=lambda r: r['gas_fraction'])
        # exact direct samples, deduplicated by (u, gas_fraction)
        seen_direct = set()
        for row in group:
            r = row.get('radius_earth')
            if row.get('status') == 'PASS_CONDITIONAL_NUMERICAL' and r is not None and math.isfinite(r) and r == target:
                key = (u, row['gas_fraction'])
                if key not in seen_direct:
                    seen_direct.add(key)
                    result = {
                        'u': u,
                        'gas_fraction': row['gas_fraction'],
                        'kind': 'DIRECT_SAMPLE',
                        'radius_earth': r,
                        'target_radius_earth': target,
                    }
                    # ALWAYS recompute fractions from u and gas_fraction
                    g = row['gas_fraction']
                    result['fractions'] = [(1 - g) * u, 0, (1 - g) * (1 - u), g]
                    results.append(result)
        # interpolate between adjacent pairs
        for i in range(len(group) - 1):
            a, b = group[i], group[i + 1]
            ra, rb = a.get('radius_earth'), b.get('radius_earth')
            if a.get('status') != 'PASS_CONDITIONAL_NUMERICAL' or b.get('status') != 'PASS_CONDITIONAL_NUMERICAL':
                continue
            if ra is None or rb is None or not (math.isfinite(ra) and math.isfinite(rb)):
                continue
            if (ra - target) * (rb - target) >= 0:
                continue
            ga, gb = a['gas_fraction'], b['gas_fraction']
            if ga <= 0 or gb <= 0 or not (math.isfinite(ga) and math.isfinite(gb)):
                continue
            # avoid division by zero if same gas fraction (should not happen due to sorting but check)
            if ga == gb:
                continue
            log_ga, log_gb = math.log(ga), math.log(gb)
            slope = (rb - ra) / (log_gb - log_ga)
            if slope == 0:
                continue
            log_g = log_ga + (target - ra) / slope
            g_interp = math.exp(log_g)
            # compute fractions for interpolated point
            fractions = [
                (1 - g_interp) * u,
                0,
                (1 - g_interp) * (1 - u),
                g_interp,
            ]
            results.append({
                'u': u,
                'gas_fraction': g_interp,
                'kind': 'INTERPOLATED_UNCONFIRMED',
                'radius_earth': None,
                'target_radius_earth': target,
                'fractions': fractions,
            })
    return results


def config_text(fractions, mass_earth, profile_native, output_native, tight=False):
    """Generate configuration text for the native solver.

    fractions: list of 4 mass fractions [core, mantle, water, gas]
    mass_earth: total planet mass in Earth masses (M_Earth)
    profile_native: path to native profile input file (absolute, no whitespace)
    output_native: path to native output file (absolute, no whitespace)
    tight: if True, use tighter tolerances for some parameters
    Returns string with lines in key=value format, ending with newline.
    """
    if len(fractions) != 4 or fractions[1] != 0:
        raise ValueError("invalid fractions")
    for f in fractions:
        if not math.isfinite(f) or f < 0:
            raise ValueError("bad fraction")
    if abs(sum(fractions) - 1) > 1e-14:
        raise ValueError("fractions do not sum to 1")
    if mass_earth <= 0 or not math.isfinite(mass_earth):
        raise ValueError("invalid mass")
    for path in (profile_native, output_native):
        if not path or any(c.isspace() for c in path):
            raise ValueError("path contains whitespace")
        # ensure absolute path: starts with '/' or X: drive (for windows)
        if not (path.startswith('/') or (len(path) > 1 and path[1] == ':')):
            raise ValueError("path not absolute")
        # reject embedded quotes/newlines
        if '"' in path or '\'' in path or '\n' in path or '\r' in path:
            raise ValueError("path contains quotes or newlines")
    ode_eps_rel1 = 1e-11 if tight else 1e-10
    fit_eps_rel = 1e-7 if tight else 1e-6
    lines = [
        'input_mode=0',
        'mass_of_core=%.17g' % (fractions[0] * mass_earth),
        'mass_of_mantle=%.17g' % (fractions[1] * mass_earth),
        'mass_of_hydro=%.17g' % (fractions[2] * mass_earth),
        'mass_of_atm=%.17g' % (fractions[3] * mass_earth),
        'surface_temp=350',
        'temp_jump_1=0',
        'temp_jump_2=0',
        'temp_jump_3=0',
        'output_file="%s"' % output_native,
        'verbose=false',
        'P_surface=100000',
        'core_phasedgm="Fe_default"',
        'mantle_phasedgm="Si_default"',
        'hydro_phasedgm="water_default"',
        'atm_phasedgm="gas_hhe_prescribed"',
        'ave_rho_core=15',
        'ave_rho_mantle=5',
        'ave_rho_hydro=2',
        'ave_rho_atm=.001',
        'rho_eps_rel=1e-11',
        'T_eps_rel=1e-11',
        'ode_eps_rel0=1e-7',
        'ode_eps_rel1=%.17g' % ode_eps_rel1,
        'R_eps_rel=2e-5',
        'ode_eps_rel2=1e-10',
        'P_eps_rel=1e-10',
        'fit_eps_rel=%.17g' % fit_eps_rel,
        'tp_profile_file="%s"' % profile_native,
    ]
    return '\n'.join(lines) + '\n'
