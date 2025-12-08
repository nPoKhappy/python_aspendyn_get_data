import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

data_filename = 'air2(8.13~17.4219)t2(140~240)acid_gas(121~160)_rerun1.csv'

output_directory = 'plots_air2_t2_rerun1'

# Input CSV (your steady-state data)
CSV_PATH = os.path.join('csv', 'my_own_data', data_filename)

# Output directory for plots
OUT_DIR = os.path.join('csv', 'my_own_data', output_directory)
os.makedirs(OUT_DIR, exist_ok=True)

# How many plots to save (each plot has two subplots)
N_PLOTS = 14

# 3D view angles (elev, azim)
H2SMF_VIEW = (35, 120)
SO2MF_VIEW = (20, 110)

# X-axis conversion: new_x = 17.228 * old_x - 0.09
# Maps 8.13 -> 140, 17.4219 -> 300
def convert_x(old_x):
    return 17.228 * old_x - 0.09


def clean_colnames(cols):
    out = []
    for c in cols:
        c = str(c)
        # collapse whitespace/newlines and strip quotes
        c = re.sub(r"\s+", " ", c).strip().strip('"').strip("'")
        out.append(c)
    return out


def find_col_by_substrings(df, substrings):
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    for sub in substrings:
        sub_l = sub.lower()
        # exact or contains
        for lc, orig in lower_map.items():
            if sub_l == lc or sub_l in lc:
                return orig
    return None


def get_single_series(df, name):
    """Return a single Series even if DataFrame has duplicate column names."""
    obj = df[name]
    if isinstance(obj, pd.DataFrame):
        return obj.iloc[:, 0]
    return obj


def make_triangulation(x, y):
    # Ensure arrays
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    # Remove duplicates to avoid Qhull errors
    xy = np.column_stack([x, y])
    _, unique_idx = np.unique(xy, axis=0, return_index=True)
    x_u = x[unique_idx]
    y_u = y[unique_idx]
    if len(x_u) < 3:
        return None
    try:
        return mtri.Triangulation(x_u, y_u)
    except Exception:
        return None


def plot_contours(dfg, x_col, y_col, z_cols, titles, suptitle, out_path, xlabel=None, ylabel=None, zlabels=None):
    n = len(z_cols)
    fig, axes = plt.subplots(1, n, figsize=(6*n, 5), constrained_layout=True)
    if n == 1:
        axes = [axes]
    # Apply x-axis conversion
    x = convert_x(dfg[x_col].values)
    y = dfg[y_col].values
    tri = make_triangulation(x, y)

    cmaps_default = ['RdYlGn_r', 'RdYlGn_r', 'RdYlGn_r', 'RdYlGn_r']
    cmaps = cmaps_default[:n]

    for i, (ax, zc, title, cmap) in enumerate(zip(axes, z_cols, titles, cmaps)):
        z = dfg[zc].values
        if tri is not None and len(z) >= 3:
            t = mtri.Triangulation(x, y)  # use original points for values
            cf = ax.tricontourf(t, z, levels=15, cmap=cmap)
            ax.scatter(x, y, c=z, cmap=cmap, s=10, edgecolor='k', linewidths=0.2, alpha=0.8)
            cb = fig.colorbar(cf, ax=ax)
            cb.set_label((zlabels[i] if zlabels else zc))
        else:
            sc = ax.scatter(x, y, c=z, cmap=cmap, s=30, edgecolor='k', linewidths=0.2)
            cb = fig.colorbar(sc, ax=ax)
            cb.set_label((zlabels[i] if zlabels else zc))
        ax.set_title(title)
        ax.set_xlabel(xlabel or x_col)
        ax.set_ylabel(ylabel or y_col)

    fig.suptitle(suptitle, fontsize=12)
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_3d_surfaces(dfg, x_col, y_col, z_cols, titles, suptitle, out_path, xlabel=None, ylabel=None, zlabels=None):
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    n = len(z_cols)
    fig = plt.figure(figsize=(6.5*n, 5))
    axes = []
    for i in range(n):
        axes.append(fig.add_subplot(1, n, i+1, projection='3d'))

    # Apply x-axis conversion
    x = convert_x(dfg[x_col].values)
    y = dfg[y_col].values

    cmaps_default = ['RdYlGn_r', 'RdYlGn_r', 'RdYlGn_r', 'RdYlGn_r']
    cmaps = cmaps_default[:n]

    for i, (ax, zc, title, cmap) in enumerate(zip(axes, z_cols, titles, cmaps)):
        z = dfg[zc].values
        tri = make_triangulation(x, y)
        if tri is not None and len(z) >= 3:
            # Rebuild tri with original points index mapping
            t = mtri.Triangulation(x, y)
            surf = ax.plot_trisurf(t, z, cmap=cmap, linewidth=0.2, antialiased=True, edgecolor='none')
            fig.colorbar(surf, ax=ax, shrink=0.6, pad=0.1, label=(zlabels[i] if zlabels else zc))
        else:
            pts = ax.scatter(x, y, z, c=z, cmap=cmap, s=10)
            fig.colorbar(pts, ax=ax, shrink=0.6, pad=0.1, label=(zlabels[i] if zlabels else zc))
        ax.set_title(title)
        ax.set_xlabel(xlabel or x_col)
        ax.set_ylabel(ylabel or y_col)
        ax.set_zlabel((zlabels[i] if zlabels else zc))
        # Different angle for H2SMF (first subplot); others use SO2MF view
        elev, azim = (H2SMF_VIEW if i == 0 else SO2MF_VIEW)
        ax.view_init(elev=elev, azim=azim)

    fig.suptitle(suptitle, fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# Helper to sanitize strings used in filenames
def safe_component(s):
    return re.sub(r"[^\w\-\.]+", "_", str(s)).strip('_')


def main():
    # Load CSV (handle odd headers/newlines)
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig', engine='python')

    # Clean column names
    df.columns = clean_colnames(df.columns)

    # Detect needed columns
    col_air2 = find_col_by_substrings(df, ['AIR2'])
    col_t2 = find_col_by_substrings(df, ['T2'])
    col_h2smf = find_col_by_substrings(df, ['H2SMF'])
    col_so2mf = find_col_by_substrings(df, ['SO2MF'])

    if not all([col_air2, col_t2, col_h2smf, col_so2mf]):
        missing = {
            'AIR2': col_air2,
            'T2': col_t2,
            'H2SMF': col_h2smf,
            'SO2MF': col_so2mf,
        }
        raise RuntimeError(f"Missing required columns (after cleaning): {missing}")

    # Prefer ACID_GAS-like grouping
    col_group = find_col_by_substrings(df, ['ACID_GAS', 'ACID GAS', 'ACIDGAS'])
    if col_group is None:
        # fallback: try Description
        col_group = find_col_by_substrings(df, ['Description'])
    if col_group is None:
        # if no group column, create a single group value so we can still plot
        col_group = '__GROUP__'
        df[col_group] = 'ALL'

    # Build internal numeric columns to avoid duplicate-name ambiguity
    x_ser = pd.to_numeric(get_single_series(df, col_air2), errors='coerce')
    y_ser = pd.to_numeric(get_single_series(df, col_t2), errors='coerce')
    z1_ser = pd.to_numeric(get_single_series(df, col_h2smf), errors='coerce')
    z2_ser = pd.to_numeric(get_single_series(df, col_so2mf), errors='coerce')

    df_aug = df.copy()
    XCOL, YCOL, Z1COL, Z2COL = '__AIR2__', '__T2__', '__H2SMF__', '__SO2MF__'
    df_aug[XCOL] = x_ser
    df_aug[YCOL] = y_ser
    df_aug[Z1COL] = z1_ser
    df_aug[Z2COL] = z2_ser
    # Compute Total S = H2SMF + SO2MF
    TOTALCOL = '__TOTAL_S__'
    df_aug[TOTALCOL] = df_aug[Z1COL] + df_aug[Z2COL]

    # Keep only valid rows
    df_valid = df_aug.dropna(subset=[XCOL, YCOL, Z1COL, Z2COL]).copy()
    if df_valid.empty:
        raise RuntimeError('No valid rows after numeric coercion.')

    # If grouping by ACID_GAS (or variants), use the 14 specified values; otherwise, fall back to unique groups
    desired_groups = [121, 124, 127, 130, 133, 136, 139, 142, 145, 148, 151, 154, 157, 160]

    use_desired = any(k in col_group.lower() for k in ['acid_gas', 'acidgas', 'acid gas'])

    if use_desired:
        print(f"Using specified {col_group} groups: {desired_groups}")
        group_numeric = pd.to_numeric(get_single_series(df_valid, col_group), errors='coerce')
        groups_iter = desired_groups
    else:
        # Determine groups (take first N_PLOTS unique values)
        group_series = get_single_series(df_valid, col_group)
        groups = pd.unique(group_series)
        try:
            groups_iter = sorted(groups, key=lambda x: float(x))
        except Exception:
            groups_iter = sorted(groups, key=lambda x: str(x))
        if len(groups_iter) > N_PLOTS:
            groups_iter = groups_iter[:N_PLOTS]
        print(f"Using group column: {col_group}. Total groups found: {len(groups)}. Generating {len(groups_iter)} groups.")
        group_numeric = pd.to_numeric(group_series, errors='coerce')

    saved_contour = 0
    saved_3d = 0
    missing = []

    safe_col_group = safe_component(col_group)

    for g in groups_iter:
        # Select rows for this group
        if pd.api.types.is_numeric_dtype(group_numeric):
            mask = np.isclose(group_numeric.values, float(g), atol=1e-6)
            dfg = df_valid.loc[mask]
        else:
            dfg = df_valid[get_single_series(df_valid, col_group) == g]

        if dfg.empty:
            missing.append(g)
            continue

        # 2D contour figure (two subplots: H2SMF, SO2MF)
        safe_g = safe_component(g)
        fname_contour = f"air2_t2_{safe_col_group}_{safe_g}_H2SMF_SO2MF_contour.png"
        out_contour = os.path.join(OUT_DIR, fname_contour)
        plot_contours(
            dfg,
            XCOL,
            YCOL,
            [Z1COL, Z2COL],
            ['H2SMF (2D Contour)', 'SO2MF (2D Contour)'],
            f'{col_group} = {g}',
            out_contour,
            xlabel='AIR2 ($m^3$)',
            ylabel=col_t2,
            zlabels=[col_h2smf, col_so2mf],
        )
        saved_contour += 1
        print(f"Saved contour: {out_contour} ({len(dfg)} points)")

        # Additional 2D contour for Total S
        fname_contour_total = f"air2_t2_{safe_col_group}_{safe_g}_TotalS_contour.png"
        out_contour_total = os.path.join(OUT_DIR, fname_contour_total)
        plot_contours(
            dfg,
            XCOL,
            YCOL,
            [TOTALCOL],
            ['Total S (2D Contour)'],
            f'{col_group} = {g}',
            out_contour_total,
            xlabel='AIR2 ($m^3$)',
            ylabel=col_t2,
            zlabels=['Total S'],
        )
        print(f"Saved contour (Total S): {out_contour_total} ({len(dfg)} points)")

        # 3D surface figure (two subplots: H2SMF, SO2MF)
        fname_3d = f"air2_t2_{safe_col_group}_{safe_g}_H2SMF_SO2MF_3D.png"
        out_3d = os.path.join(OUT_DIR, fname_3d)
        plot_3d_surfaces(
            dfg,
            XCOL,
            YCOL,
            [Z1COL, Z2COL],
            ['H2SMF (3D Surface)', 'SO2MF (3D Surface)'],
            f'{col_group} = {g}',
            out_3d,
            xlabel='AIR2 ($m^3$)',
            ylabel=col_t2,
            zlabels=[col_h2smf, col_so2mf],
        )
        saved_3d += 1
        print(f"Saved 3D: {out_3d} ({len(dfg)} points)")

        # Additional 3D surface for Total S
        fname_3d_total = f"air2_t2_{safe_col_group}_{safe_g}_TotalS_3D.png"
        out_3d_total = os.path.join(OUT_DIR, fname_3d_total)
        plot_3d_surfaces(
            dfg,
            XCOL,
            YCOL,
            [TOTALCOL],
            ['Total S (3D Surface)'],
            f'{col_group} = {g}',
            out_3d_total,
            xlabel='AIR2 ($m^3$)',
            ylabel=col_t2,
            zlabels=['Total S'],
        )
        print(f"Saved 3D (Total S): {out_3d_total} ({len(dfg)} points)")

    if use_desired and missing:
        print(f"Warning: Missing groups (no rows found): {missing}")

    print(f"Done. Saved {saved_contour} contour figure(s) and {saved_3d} 3D figure(s) to {OUT_DIR}.")


if __name__ == '__main__':
    main()
