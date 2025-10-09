import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from mpl_toolkits.mplot3d import Axes3D

# --- Settings ---
PROJECT_NAME = 'senpai_data'
csv_file = os.path.join('csv', PROJECT_NAME, 'fig_8.csv')

# Check if file exists
if not os.path.exists(csv_file):
    print(f"Error: Cannot find file '{csv_file}'")
    print("Please confirm the file path is correct.")
else:
    print(f"Reading file: {csv_file}")
    
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    # Display column names
    print(f"\nAvailable columns:")
    for i, col in enumerate(df.columns):
        print(f"  {i}: {col}")
    
    # Extract x and y data
    x = df['Air2 [m³/h]'].values
    y = df['T2 [℃]'].values
    
    # Select variable to plot - only Total S
    var_name = 'total S[%]'
    plot_title = 'Total Sulfur Content'
    cbar_label = 'Total S [%]'
    fmt = '.6f'
    
    z = df[var_name].values
    
    print(f"\n{'='*50}")
    print(f"Processing: {plot_title}")
    print(f"{'='*50}")
    print(f"Air2: {x.min():.2f} - {x.max():.2f} m³/h")
    print(f"T2: {y.min():.2f} - {y.max():.2f} °C")
    print(f"{cbar_label}: {z.min():{fmt}} - {z.max():{fmt}}")
    print(f"{cbar_label} range: {z.max() - z.min():{fmt}}")
    print(f"Total data points: {len(x)}")
    
    # ========== 2D Contour Plot ==========
    fig1, ax1 = plt.subplots(figsize=(12, 10))
    
    # Create more contour levels to show small variations
    num_levels = 50
    contour = ax1.tricontourf(x, y, z, levels=num_levels, cmap='RdYlGn_r')
    contour_lines = ax1.tricontour(x, y, z, levels=15, colors='black', 
                                   linewidths=0.8, alpha=0.4)
    ax1.clabel(contour_lines, inline=True, fontsize=9, fmt=f'%{fmt}', inline_spacing=10)
    
    # Add colorbar with better formatting for small values
    cbar = plt.colorbar(contour, ax=ax1, format=f'%{fmt}')
    cbar.set_label(cbar_label, fontsize=12, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)
    
    # Add text showing the range
    range_text = f'Range: {z.min():{fmt}} - {z.max():{fmt}}\nΔ = {z.max()-z.min():{fmt}}'
    ax1.text(0.02, 0.98, range_text, transform=ax1.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Set labels and title
    ax1.set_xlabel('Air2 [m³/h]', fontsize=13)
    ax1.set_ylabel('T2 [°C]', fontsize=13)
    ax1.set_title(f'2D Contour Plot: {plot_title}', fontsize=15, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add original range boundaries
    ax1.axvline(x=150, color='red', linestyle='--', alpha=0.4, linewidth=2, label='Original X Range')
    ax1.axvline(x=300, color='red', linestyle='--', alpha=0.4, linewidth=2)
    ax1.axhline(y=140, color='orange', linestyle='--', alpha=0.4, linewidth=2, label='Original Y Range')
    ax1.axhline(y=240, color='orange', linestyle='--', alpha=0.4, linewidth=2)
    
    ax1.legend(loc='upper right')
    plt.tight_layout()
    
    # Save 2D plot
    save_path_2d = os.path.join('csv', PROJECT_NAME, 'contour_plot_totalS_2D.png')
    plt.savefig(save_path_2d, dpi=300, bbox_inches='tight')
    print(f"\nSaved 2D plot: {save_path_2d}")
    
    plt.show()
    
    # ========== 3D Surface Plot ==========
    fig2 = plt.figure(figsize=(14, 10))
    ax2 = fig2.add_subplot(111, projection='3d')
    
    # Create 3D surface plot
    surf = ax2.plot_trisurf(x, y, z, cmap='RdYlGn_r', linewidth=0.1, antialiased=True, alpha=0.9)
    
    # Add colorbar
    cbar3d = fig2.colorbar(surf, ax=ax2, format=f'%{fmt}', shrink=0.5, aspect=10)
    cbar3d.set_label(cbar_label, fontsize=12, fontweight='bold')
    
    # Set labels and title
    ax2.set_xlabel('Air2 [m³/h]', fontsize=12, labelpad=10)
    ax2.set_ylabel('T2 [°C]', fontsize=12, labelpad=10)
    ax2.set_zlabel('Total S [%]', fontsize=12, labelpad=10)
    ax2.set_title(f'3D Surface Plot: {plot_title}', fontsize=15, fontweight='bold', pad=20)
    
    # Set viewing angle
    ax2.view_init(elev=25, azim=45)
    
    # Add grid
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save 3D plot
    save_path_3d = os.path.join('csv', PROJECT_NAME, 'contour_plot_totalS_3D.png')
    plt.savefig(save_path_3d, dpi=300, bbox_inches='tight')
    print(f"Saved 3D plot: {save_path_3d}")
    
    plt.show()
