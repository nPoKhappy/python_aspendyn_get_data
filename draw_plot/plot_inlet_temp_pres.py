# 註解: 此程式碼用於繪製不同入口溫度和壓力組合下的 Total S 等高線圖和 3D 表面圖
# 資料來源: air2(8.13~17.4219)t2(140~240)acid_gas(121~160)_different_inlet_temp_pres.csv
# 只繪製 acidgas_Fm = 141.526316 (最接近工廠條件)
# 每個 T-P 組合為 20x20 點

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

# --- Settings ---
data_filename = 'air2(8.13~17.4219)t2(140~240)acid_gas(121~160)_different_inlet_temp_pres.csv'
output_directory = 'plots_inlet_temp_pres'

# Input CSV path
CSV_PATH = os.path.join('csv', 'my_own_data', data_filename)

# Output directory for plots
OUT_DIR = os.path.join('csv', 'my_own_data', output_directory)
os.makedirs(OUT_DIR, exist_ok=True)

# Filter by acidgas_Fm (closest to factory condition)
ACIDGAS_FM_TARGET = 141.526316

# X-axis conversion: new_x = 17.228 * old_x - 0.09
# Maps 8.13 -> 140, 17.4219 -> 300
def convert_x(old_x):
    return 17.228 * old_x - 0.09


def clean_colnames(cols):
    out = []
    for c in cols:
        c = str(c)
        c = re.sub(r"\s+", " ", c).strip().strip('"').strip("'")
        c = c.replace('_x000D_', '').strip()
        out.append(c)
    return out


def find_col_by_substrings(df, substrings):
    cols = list(df.columns)
    lower_map = {c.lower().replace(' ', '').replace('_', ''): c for c in cols}
    for sub in substrings:
        sub_l = sub.lower().replace(' ', '').replace('_', '')
        for lc, orig in lower_map.items():
            if sub_l == lc or sub_l in lc:
                return orig
    return None


def make_triangulation(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
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


def plot_contour_and_3d(dfg, x_col, y_col, z_col, suptitle, out_path_prefix, xlabel='Air2 [m³/h]', ylabel='T2 [°C]', zlabel='Total S'):
    """Plot 2D contour and 3D surface for a single T-P combination"""
    
    # Apply x-axis conversion
    x = convert_x(dfg[x_col].values)
    y = dfg[y_col].values
    z = dfg[z_col].values
    
    # Remove NaN
    valid = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
    x, y, z = x[valid], y[valid], z[valid]
    
    print(f"  Data points: {len(x)}")
    print(f"  X range: {x.min():.2f} - {x.max():.2f}")
    print(f"  Y range: {y.min():.2f} - {y.max():.2f}")
    print(f"  Z range: {z.min():.6f} - {z.max():.6f}")
    
    # ========== 2D Contour Plot ==========
    fig1, ax1 = plt.subplots(figsize=(12, 10))
    
    tri = make_triangulation(x, y)
    if tri is not None and len(z) >= 3:
        t = mtri.Triangulation(x, y)
        contour = ax1.tricontourf(t, z, levels=50, cmap='RdYlGn_r')
        contour_lines = ax1.tricontour(t, z, levels=15, colors='black', linewidths=0.8, alpha=0.4)
        ax1.clabel(contour_lines, inline=True, fontsize=9, fmt='%.6f', inline_spacing=10)
    else:
        contour = ax1.scatter(x, y, c=z, cmap='RdYlGn_r', s=30, edgecolor='k', linewidths=0.2)
    
    cbar = plt.colorbar(contour, ax=ax1, format='%.6f')
    cbar.set_label(zlabel, fontsize=12, fontweight='bold')
    
    # Add range text
    range_text = f'Range: {z.min():.6f} - {z.max():.6f}\nΔ = {z.max()-z.min():.6f}'
    ax1.text(0.02, 0.98, range_text, transform=ax1.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax1.set_xlabel(xlabel, fontsize=13)
    ax1.set_ylabel(ylabel, fontsize=13)
    ax1.set_title(f'2D Contour Plot: {suptitle}', fontsize=15, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add reference boundaries
    ax1.axvline(x=140, color='red', linestyle='--', alpha=0.4, linewidth=2)
    ax1.axvline(x=300, color='red', linestyle='--', alpha=0.4, linewidth=2)
    ax1.axhline(y=140, color='orange', linestyle='--', alpha=0.4, linewidth=2)
    ax1.axhline(y=240, color='orange', linestyle='--', alpha=0.4, linewidth=2)
    
    plt.tight_layout()
    save_path_2d = f"{out_path_prefix}_2D.png"
    fig1.savefig(save_path_2d, dpi=300, bbox_inches='tight')
    print(f"  Saved: {save_path_2d}")
    plt.close(fig1)
    
    # ========== 3D Surface Plot ==========
    fig2 = plt.figure(figsize=(14, 10))
    ax2 = fig2.add_subplot(111, projection='3d')
    
    if tri is not None and len(z) >= 3:
        t = mtri.Triangulation(x, y)
        surf = ax2.plot_trisurf(t, z, cmap='RdYlGn_r', linewidth=0.1, antialiased=True, alpha=0.8)
    else:
        surf = ax2.scatter(x, y, z, c=z, cmap='RdYlGn_r', s=10)
    
    cbar3d = fig2.colorbar(surf, ax=ax2, format='%.6f', shrink=0.5, aspect=10)
    cbar3d.set_label(zlabel, fontsize=12, fontweight='bold')
    
    ax2.set_xlabel(xlabel, fontsize=12, labelpad=10)
    ax2.set_ylabel(ylabel, fontsize=12, labelpad=10)
    ax2.set_zlabel(zlabel, fontsize=12, labelpad=10)
    ax2.set_title(f'3D Surface Plot: {suptitle}', fontsize=15, fontweight='bold', pad=20)
    ax2.view_init(elev=25, azim=45)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_path_3d = f"{out_path_prefix}_3D.png"
    fig2.savefig(save_path_3d, dpi=300, bbox_inches='tight')
    print(f"  Saved: {save_path_3d}")
    plt.close(fig2)


def main():
    # Check if file exists
    if not os.path.exists(CSV_PATH):
        print(f"Error: Cannot find file '{CSV_PATH}'")
        return
    
    print(f"Reading file: {CSV_PATH}")
    
    # Read CSV
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    df.columns = clean_colnames(df.columns)
    
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Find columns
    col_x = find_col_by_substrings(df, ['air2_SP', 'air2sp'])
    col_y = find_col_by_substrings(df, ['HEATER2_output_T_SP', 'heater2outputtsp'])
    col_z = find_col_by_substrings(df, ['Total_S', 'totals'])
    col_acidgas_fm = find_col_by_substrings(df, ['acidgas_Fm', 'acidgasfm'])
    col_acidgas_t = find_col_by_substrings(df, ['acidgas_T', 'acidgast'])
    col_acidgas_p = find_col_by_substrings(df, ['acidgas_P', 'acidgasp'])
    
    print(f"\nUsing columns:")
    print(f"  X (air2_SP): {col_x}")
    print(f"  Y (HEATER2_output_T_SP): {col_y}")
    print(f"  Z (Total_S): {col_z}")
    print(f"  acidgas_Fm: {col_acidgas_fm}")
    print(f"  acidgas_T: {col_acidgas_t}")
    print(f"  acidgas_P: {col_acidgas_p}")
    
    # Filter by acidgas_Fm (closest to factory condition)
    df_filtered = df[np.isclose(df[col_acidgas_fm], ACIDGAS_FM_TARGET, atol=0.01)].copy()
    print(f"\nFiltered by acidgas_Fm = {ACIDGAS_FM_TARGET}")
    print(f"  Rows after filter: {len(df_filtered)}")
    
    if df_filtered.empty:
        print("Error: No data found for the specified acidgas_Fm value")
        return
    
    # Get unique T-P combinations
    tp_combinations = df_filtered[[col_acidgas_t, col_acidgas_p]].drop_duplicates()
    print(f"\nFound {len(tp_combinations)} T-P combinations:")
    
    # Plot for each T-P combination
    for idx, row in tp_combinations.iterrows():
        t_val = row[col_acidgas_t]
        p_val = row[col_acidgas_p]
        
        print(f"\n{'='*60}")
        print(f"Processing: T = {t_val}°C, P = {p_val} bar")
        print(f"{'='*60}")
        
        # Filter data for this T-P combination
        mask = (np.isclose(df_filtered[col_acidgas_t], t_val, atol=0.001) & 
                np.isclose(df_filtered[col_acidgas_p], p_val, atol=0.0001))
        dfg = df_filtered[mask].copy()
        
        # Create title and filename
        suptitle = f'Total S (acidgas_Fm={ACIDGAS_FM_TARGET:.2f}, T={t_val}°C, P={p_val:.3f}bar)'
        safe_name = f"T{t_val}_P{p_val:.4f}".replace('.', '_')
        out_path_prefix = os.path.join(OUT_DIR, f"totalS_{safe_name}")
        
        # Plot
        plot_contour_and_3d(dfg, col_x, col_y, col_z, suptitle, out_path_prefix)
    
    print(f"\n{'='*60}")
    print(f"ALL PLOTS COMPLETED!")
    print(f"Output directory: {OUT_DIR}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
