import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import os

# --- Settings ---
# Change this to your CSV file path
csv_file = os.path.join('csv', 'my_own_data', 'air2(8.13~17.4219_40pts)t2(140~240_40pts)acid_gas(121~160_3pts).csv')  # Update filename as needed

# Points to label on the 3D plot (x=air2_SP_m3, y=HEATER2_output_T_SP)
label_points = [
    (270, 230),
    (270, 178),
    (270, 155),
    (223, 155),
    (190, 155),
    (190, 178),
    (190, 230),
    (223, 230),
]
# Filter by acidgas_Fm values (all three categories)
ACIDGAS_FM_FILTERS = [121, 140.5, 160]

# Check if file exists
if not os.path.exists(csv_file):
    print(f"Error: Cannot find file '{csv_file}'")
    print("Please update the csv_file path to your actual file.")
else:
    print(f"Reading file: {csv_file}")
    
    # Read CSV file
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    
    # Strip whitespace and clean column names
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True).str.replace('_x000D_', '', regex=False)
    df.columns = df.columns.str.strip()
    
    # Display column names
    print(f"\nAvailable columns:")
    for i, col in enumerate(df.columns):
        print(f"  {i}: '{col}'")
    
    # Find columns (flexible matching)
    def find_col(df, keywords):
        for col in df.columns:
            col_lower = col.lower().replace(' ', '').replace('_', '')
            for kw in keywords:
                if kw.lower().replace(' ', '').replace('_', '') in col_lower:
                    return col
        return None
    
    col_x = find_col(df, ['air2_SP_m3', 'air2_sp_m3', 'air2spm3'])
    col_y = find_col(df, ['HEATER2_output_T_SP', 'heater2_output_t_sp', 'heater2outputtsp'])
    col_z = find_col(df, ['Total_S', 'total_s', 'totals'])
    
    # Fallback: try by position if not found
    if col_x is None:
        col_x = df.columns[1] if len(df.columns) > 1 else None
        print(f"Warning: Using column '{col_x}' as x (air2_SP_m3)")
    if col_y is None:
        col_y = df.columns[0] if len(df.columns) > 0 else None
        print(f"Warning: Using column '{col_y}' as y (HEATER2_output_T_SP)")
    if col_z is None:
        col_z = df.columns[-1] if len(df.columns) > 0 else None
        print(f"Warning: Using column '{col_z}' as z (Total_S)")
    
    print(f"\nUsing columns:")
    print(f"  X (air2_SP_m3): '{col_x}'")
    print(f"  Y (HEATER2_output_T_SP): '{col_y}'")
    print(f"  Z (Total_S): '{col_z}'")
    
    # Find acidgas_Fm column and filter
    col_acidgas = find_col(df, ['acidgas_Fm', 'acidgasfm', 'acidgas_fm'])
    if col_acidgas is None:
        col_acidgas = 'acidgas_Fm'  # fallback
    
    df[col_acidgas] = pd.to_numeric(df[col_acidgas], errors='coerce')
    
    # ========== 3D Surface Plots for all categories ==========
    fig = plt.figure(figsize=(20, 6))
    
    for plot_idx, ACIDGAS_FM_VALUE in enumerate(ACIDGAS_FM_FILTERS):
        df_filtered = df[np.isclose(df[col_acidgas], ACIDGAS_FM_VALUE, atol=0.5)].copy()
        print(f"\nFiltering by {col_acidgas} = {ACIDGAS_FM_VALUE}")
        print(f"  Rows after filter: {len(df_filtered)} (from {len(df)})")
        
        if df_filtered.empty:
            print(f"Error: No data found for {col_acidgas} = {ACIDGAS_FM_VALUE}")
            continue
        
        # Extract data from filtered dataframe
        x = pd.to_numeric(df_filtered[col_x], errors='coerce').values
        y = pd.to_numeric(df_filtered[col_y], errors='coerce').values
        z = pd.to_numeric(df_filtered[col_z], errors='coerce').values
    
        # Remove NaN
        valid = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
        x, y, z = x[valid], y[valid], z[valid]
        
        print(f"  Data range:")
        print(f"    X (air2_SP_m3): {x.min():.2f} - {x.max():.2f}")
        print(f"    Y (HEATER2_output_T_SP): {y.min():.2f} - {y.max():.2f}")
        print(f"    Z (Total_S): {z.min():.6f} - {z.max():.6f}")
        print(f"    Total valid points: {len(x)}")
        
        # Create subplot
        ax = fig.add_subplot(1, 3, plot_idx + 1, projection='3d')
        
        # Create 3D surface plot
        surf = ax.plot_trisurf(x, y, z, cmap='RdYlGn_r', linewidth=0.1, antialiased=True, alpha=0.5)
        
        # Add colorbar
        cbar = fig.colorbar(surf, ax=ax, format='%.6f', shrink=0.5, aspect=10)
        cbar.set_label('Total S', fontsize=10, fontweight='bold')
        
        # Label the specified points
        for (px, py) in label_points:
            # Find closest point in data
            distances = np.sqrt((x - px)**2 + (y - py)**2)
            idx = np.argmin(distances)
            pz = z[idx]
            actual_x, actual_y = x[idx], y[idx]
            
            # Plot marker
            ax.scatter([actual_x], [actual_y], [pz], color='blue', s=60, edgecolor='black', linewidth=1.5, zorder=5)
            
            # Add label
            label_text = f'({px}, {py})\nZ={pz:.6f}'
            ax.text(actual_x, actual_y, pz + (z.max() - z.min()) * 0.05, label_text,
                    fontsize=7, ha='center', va='bottom', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8))
        
        # Set labels and title
        ax.set_xlabel('air2_SP_m3 [m³/h]', fontsize=10, labelpad=8)
        ax.set_ylabel('HEATER2_output_T_SP [°C]', fontsize=10, labelpad=8)
        ax.set_zlabel('Total S', fontsize=10, labelpad=8)
        ax.set_title(f'acidgas_Fm = {ACIDGAS_FM_VALUE}', fontsize=12, fontweight='bold', pad=10)
        
        # Set viewing angle
        ax.view_init(elev=25, azim=45)
        
        # Add grid
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('3D Surface Plot: Total S vs Air2 and T2', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()
    
    print("\nPlot displayed (not saved).")
