import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import warnings

# Ignore minor warnings to keep logs clean
warnings.filterwarnings('ignore')

file_path = r"c:\Users\Administrator\Desktop\python_aspendyn_get_data\csv\my_own_data\air2(2.94~35.24_110pts)t2(180~200_5pts)acid_gas(135_145_10pts).csv"

# 讀取 CSV 檔案
df = pd.read_csv(file_path)

# 過濾掉錯誤與確保資料為數值
df = df[df['Status'] == 'OK']
for col in ['air2_SP', 'H2SOUT', 'SO2OUT', 'acidgas_Fm', 'HEATER2_output_T_SP']:
    df[col] = pd.to_numeric(df[col])

unique_acidgas = sorted(df['acidgas_Fm'].unique())
base_plot_dir = r"c:\Users\Administrator\Desktop\python_aspendyn_get_data\csv\my_own_data\plots_all_acidgas"
os.makedirs(base_plot_dir, exist_ok=True)
cmap = 'RdYlGn_r'

def create_plots_for_acidgas(fixed_acidgas):
    df_fixed = df[df['acidgas_Fm'] == fixed_acidgas]
    
    # 建立此流量專屬的資料夾
    acidgas_str = f"{fixed_acidgas:.2f}"
    folder_path = os.path.join(base_plot_dir, f"acidgas_Fm_{acidgas_str}")
    os.makedirs(folder_path, exist_ok=True)
    
    for z_col in ['H2SOUT', 'SO2OUT']:
        pivot_df = df_fixed.pivot_table(values=z_col, index='HEATER2_output_T_SP', columns='air2_SP', aggfunc='mean')
        
        # 使用內插法補齊因為 Status == 'Errors' 導致的空值(破洞)
        pivot_df = pivot_df.interpolate(axis=1, limit_direction='both').interpolate(axis=0, limit_direction='both')
        
        pivot_df = pivot_df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        
        if pivot_df.shape[0] < 2 or pivot_df.shape[1] < 2:
            continue
            
        X = pivot_df.columns.values
        Y = pivot_df.index.values
        X, Y = np.meshgrid(X, Y)
        Z = pivot_df.values

        # 1. 2D Contour
        fig1 = plt.figure(figsize=(9, 7))
        ax1 = fig1.add_subplot(111)
        contour_f = ax1.contourf(X, Y, Z, levels=40, cmap=cmap)
        
        try:
            contour_lines = ax1.contour(X, Y, Z, levels=15, colors='black', linewidths=0.5, alpha=0.6)
            ax1.clabel(contour_lines, inline=True, fontsize=8, fmt='%.4f', colors='black')
        except Exception:
            pass
            
        ax1.set_xlabel('Air2 SP (X)', fontsize=12)
        ax1.set_ylabel('TR2 (Y, °C)', fontsize=12)
        ax1.set_title(f'2D Contour: {z_col} (acidgas_Fm={acidgas_str})', fontsize=14, fontweight='bold')
        ax1.grid(True, linestyle='-', alpha=0.3)
        
        z_min, z_max = np.nanmin(Z), np.nanmax(Z)
        delta_z = z_max - z_min
        textbox_str = f"Range: {z_min:.4f} - {z_max:.4f}\n$\\Delta$ = {delta_z:.4f}"
        props = dict(boxstyle='round', facecolor='white', edgecolor='black', alpha=0.9)
        ax1.text(0.05, 0.95, textbox_str, transform=ax1.transAxes, fontsize=10, verticalalignment='top', bbox=props)
        fig1.colorbar(contour_f, ax=ax1, pad=0.05).set_label(z_col, fontsize=12, fontweight='bold')
        
        path1 = os.path.join(folder_path, f"contour_{z_col}.png")
        fig1.tight_layout()
        fig1.savefig(path1, dpi=300)
        plt.close(fig1)

        # 2. 3D Surface
        fig2 = plt.figure(figsize=(10, 8))
        ax2 = fig2.add_subplot(111, projection='3d')
        surf = ax2.plot_surface(X, Y, Z, cmap=cmap, edgecolor='none', alpha=0.9)
        ax2.set_xlabel('Air2 SP (X)', fontsize=12, labelpad=10)
        ax2.set_ylabel('TR2 (Y, °C)', fontsize=12, labelpad=10)
        ax2.set_zlabel(z_col, fontsize=12, labelpad=10)
        ax2.set_title(f'3D Surface: {z_col} (acidgas_Fm={acidgas_str})', fontsize=14, fontweight='bold')
        ax2.view_init(elev=25, azim=-125)
        cbar2 = fig2.colorbar(surf, ax=ax2, shrink=0.5, aspect=10, pad=0.1)
        cbar2.set_label(z_col, fontsize=12, fontweight='bold')
        
        path2 = os.path.join(folder_path, f"3d_{z_col}.png")
        fig2.tight_layout()
        fig2.savefig(path2, dpi=300)
        plt.close(fig2)

print(f"Found {len(unique_acidgas)} unique acidgas_Fm values. Generating plots...")
for val in unique_acidgas:
    print(f"Generating for {val:.2f}...")
    create_plots_for_acidgas(val)

print("All plots generated successfully!")
