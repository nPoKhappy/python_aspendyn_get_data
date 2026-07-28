# 註解: 此程式碼用於從指定目錄中的多個 XLSX 文件中讀取數據，並繪製每個文件中兩個變量（second_air2 和 HEATER2_output_T_SP）之間的""時間序列軌跡圖""。
# 每個圖表顯示了數據的起點和終點，並標註了原始範圍邊界。此外，程式碼還會輸出分析的統計信息，包括文件數量和數據範圍。
# 學長論文圖八數據
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# --- Settings ---
# CSV file directory
PROJECT_NAME = 'out_of_distribution'
CSV_FOLDER_NAME = 'completed'
CSV_FILE_SUFFIX = '_new.csv'
csv_folder = os.path.join('csv', PROJECT_NAME, CSV_FOLDER_NAME)

parser = argparse.ArgumentParser(description='Plot Air2 versus T2 from CSV files.')
parser.add_argument('csv_files', nargs='*')
parser.add_argument('--no-show', action='store_true')
args = parser.parse_args()

# Check if directory exists
if not os.path.exists(csv_folder):
    print(f"Error: Cannot find directory '{csv_folder}'")
    print("Please confirm the directory path is correct.")
else:
    # Analyze explicitly requested files, or all merged files by default.
    if args.csv_files:
        csv_files = [os.path.normpath(file_name) for file_name in args.csv_files]
    else:
        csv_files = sorted(
            os.path.join(csv_folder, file_name)
            for file_name in os.listdir(csv_folder)
            if file_name.endswith(CSV_FILE_SUFFIX)
        )

    if not csv_files:
        print(f"Cannot find CSV files ending with '{CSV_FILE_SUFFIX}' in '{csv_folder}'")
    else:
        print(f"Found {len(csv_files)} CSV file")
        
        # Store all file data
        all_files_data = []
        
        # Read each CSV file
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                # Check if required columns exist
                required_columns = ['second_air2', 'HEATER2_output_T_SP']
                if all(col in df.columns for col in required_columns):
                    # Get entire time series
                    air2_series = df['second_air2'].values
                    t2_series = df['HEATER2_output_T_SP'].values
                    
                    # Store file information
                    file_data = {
                        'filename': os.path.basename(csv_file),
                        'air2': air2_series,
                        't2': t2_series
                    }
                    all_files_data.append(file_data)
                    
                    print(f"File: {os.path.basename(csv_file)} - {len(air2_series)} data points")
                else:
                    print(f"Warning: {os.path.basename(csv_file)} missing required columns")

            except Exception as e:
                print(f"Error reading file {csv_file}: {e}")
        
        if len(all_files_data) > 0:
            # Create separate charts for each file
            for i, file_data in enumerate(all_files_data):
                air2 = file_data['air2']
                t2 = file_data['t2']
                filename = file_data['filename']
                
                # Create individual chart
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Clean filename for display (remove .csv extension)
                display_name = os.path.splitext(filename)[0]
                display_title = f'File {i+1}: {display_name}'
                if len(display_title) > 55 and '_air2_' in display_name:
                    prefix, settings = display_name.rsplit('_air2_', 1)
                    display_title = f'File {i+1}: {prefix}\nair2_{settings}'
                fig.suptitle(display_title, fontsize=14, fontweight='bold')
                
                # Draw trajectory line
                ax.plot(air2, t2, color='blue', linewidth=2, alpha=0.8, marker='o', 
                       markersize=4, markerfacecolor='lightblue', markeredgecolor='blue')
                
                # Mark starting point (green circle)
                ax.scatter(air2[0], t2[0], color='green', s=150, marker='o', 
                          edgecolors='black', linewidth=2, alpha=0.9, zorder=5, label='Start')
                
                # Mark ending point (red square)
                ax.scatter(air2[-1], t2[-1], color='red', s=150, marker='s', 
                          edgecolors='black', linewidth=2, alpha=0.9, zorder=5, label='End')
                
                # Annotate start and end point values
                ax.annotate(f'Start\n({air2[0]:.1f}, {t2[0]:.1f})', 
                           (air2[0], t2[0]), xytext=(10, 10), 
                           textcoords='offset points', fontsize=10, 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
                
                ax.annotate(f'End\n({air2[-1]:.1f}, {t2[-1]:.1f})', 
                           (air2[-1], t2[-1]), xytext=(10, -20), 
                           textcoords='offset points', fontsize=10,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.7))
                
                ax.set_xlabel('Air2 Flow Rate (m³/h)', fontsize=12)
                ax.set_ylabel('T2 Temperature (°C)', fontsize=12)
                ax.set_title(f'Air2 vs T2 Time Series Trajectory\n({len(air2)} data points)', fontsize=14)
                ax.set_xlim(100, max(350, np.ceil(np.nanmax(air2) / 10) * 10))
                ax.set_ylim(100, max(300, np.ceil(np.nanmax(t2) / 10) * 10))
                ax.grid(True, alpha=0.3)
                
                # Add original range boundaries
                # Original x-axis range: 150-300
                ax.axvline(x=140, color= "black", linestyle='--', alpha=0.6, linewidth=2, label='Original X Range')
                ax.axvline(x=300, color='black', linestyle='--', alpha=0.6, linewidth=2)
                
                # Original y-axis range: 140-240  
                ax.axhline(y=140, color='black', linestyle='--', alpha=0.6, linewidth=2, label='Original Y Range')
                ax.axhline(y=240, color='black', linestyle='--', alpha=0.6, linewidth=2)
                
                # Add text annotations for the ranges
                ax.text(140, 105, 'X=140', rotation=90, fontsize=10, color='black', fontweight='bold')
                ax.text(300, 105, 'X=300', rotation=90, fontsize=10, color='black', fontweight='bold')
                ax.text(105, 140, 'Y=140', fontsize=10, color='black', fontweight='bold')
                ax.text(105, 240, 'Y=240', fontsize=10, color='black', fontweight='bold')
                
                ax.legend()
                
                plt.tight_layout(rect=[0, 0, 1, 0.88])
                
                # Save the plot beside the source CSV
                save_filename = f"plot_{i+1}_{display_name}.png"
                save_path = os.path.join(csv_folder, save_filename)
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Saved plot: {save_filename}")
                
                if not args.no_show:
                    plt.show()
                plt.close(fig)
            
            # Display statistics
            print(f"\n=== Statistics ===")
            print(f"Total analyzed files: {len(all_files_data)}")
            
            # Calculate range of all points
            all_air2_points = []
            all_t2_points = []
            total_points = 0
            
            for file_data in all_files_data:
                all_air2_points.extend(file_data['air2'])
                all_t2_points.extend(file_data['t2'])
                total_points += len(file_data['air2'])
                print(f"- {file_data['filename']}: {len(file_data['air2'])} data points")
            
            print(f"Total data points: {total_points}")
            print(f"Air2 range: {min(all_air2_points):.1f} ~ {max(all_air2_points):.1f} m3/h")
            print(f"T2 range: {min(all_t2_points):.1f} ~ {max(all_t2_points):.1f} deg C")
            
        else:
            print("No valid data found for analysis")
