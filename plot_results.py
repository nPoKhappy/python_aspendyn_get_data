import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 設定 ---
# CSV 檔案所在的資料夾和檔名
PROJECT_NAME = 'Test'
FILE_NAME = 'air2_step_change_up5_dataform.csv'

# 建立 CSV 檔案的完整路徑
csv_file_path = os.path.join('csv', PROJECT_NAME, FILE_NAME)

# --- 檢查檔案是否存在 ---
if not os.path.exists(csv_file_path):
    print(f"錯誤：找不到檔案 '{csv_file_path}'")
    print("請確認檔名和路徑是否正確，並先執行 main_claus_flow_record.py 來生成數據。")
else:
    # --- 讀取數據 ---
    df = pd.read_csv(csv_file_path)

    # 將 'j' 當作時間軸 (x軸)
    time_steps = df['j']

    # --- 圖表 1: 二次空氣 (MV) vs 尾氣 (CVs) ---
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True) # 2個子圖，共享X軸
    fig1.suptitle('Secondary Air Analysis', fontsize=16)

    # --- 子圖 1.1: 二次空氣 vs H2S ---
    ax1_twin = ax1.twinx()
    p1, = ax1.plot(time_steps, df['second_air2'], color='blue', linestyle='-', label='Secondary Air (MV)')
    ax1.set_ylabel('Air Flow (second_air2)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True)

    p2, = ax1_twin.plot(time_steps, df['B35_H2S'], color='red', label='Tail Gas H2S (CV)')
    ax1_twin.set_ylabel('H2S Concentration (ppm)', color='red')
    ax1_twin.tick_params(axis='y', labelcolor='red')
    
    ax1.set_title('Effect on Tail Gas H2S')
    ax1.legend(handles=[p1, p2], loc='upper right')

    # --- 子圖 1.2: 二次空氣 vs SO2 ---
    ax2_twin = ax2.twinx()
    p3, = ax2.plot(time_steps, df['second_air2'], color='blue', label='Secondary Air (MV)')
    ax2.set_xlabel('Time (steps)')
    ax2.set_ylabel('Air Flow (second_air2)', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')
    ax2.grid(True)

    p4, = ax2_twin.plot(time_steps, df['B35_SO2'], color='green', label='Tail Gas SO2 (CV)')
    ax2_twin.set_ylabel('SO2 Concentration (ppm)', color='green')
    ax2_twin.tick_params(axis='y', labelcolor='green')

    ax2.set_title('Effect on Tail Gas SO2')
    ax2.legend(handles=[p3, p4], loc='upper right')


    # --- 圖表 2: TR2 溫度 (MV) vs 尾氣 (CVs) ---
    fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(12, 10), sharex=True) # 2個子圖，共享X軸
    fig2.suptitle('TR2 Temperature Analysis', fontsize=16)

    # --- 子圖 2.1: TR2 vs H2S ---
    ax3_twin = ax3.twinx()
    p5, = ax3.plot(time_steps, df['HEATER2_output_T_PV'], color='blue', label='TR2 Temperature (MV)')
    ax3.set_ylabel('Temperature (°C)', color='blue')
    ax3.tick_params(axis='y', labelcolor='blue')
    ax3.grid(True)

    p6, = ax3_twin.plot(time_steps, df['B35_H2S'], color='red', label='Tail Gas H2S (CV)')
    ax3_twin.set_ylabel('H2S Concentration (ppm)', color='red')
    ax3_twin.tick_params(axis='y', labelcolor='red')

    ax3.set_title('Effect on Tail Gas H2S')
    ax3.legend(handles=[p5, p6], loc='upper right')

    # --- 子圖 2.2: TR2 vs SO2 ---
    ax4_twin = ax4.twinx()
    p7, = ax4.plot(time_steps, df['HEATER2_output_T_PV'], color='blue', label='TR2 Temperature (MV)')
    ax4.set_xlabel('Time (steps)')
    ax4.set_ylabel('Temperature (°C)', color='blue')
    ax4.tick_params(axis='y', labelcolor='blue')
    ax4.grid(True)

    p8, = ax4_twin.plot(time_steps, df['B35_SO2'], color='green', label='Tail Gas SO2 (CV)')
    ax4_twin.set_ylabel('SO2 Concentration (ppm)', color='green')
    ax4_twin.tick_params(axis='y', labelcolor='green')

    ax4.set_title('Effect on Tail Gas SO2')
    ax4.legend(handles=[p7, p8], loc='upper right')

    # --- 顯示圖表 ---
    fig1.tight_layout(rect=[0, 0, 1, 0.96])
    fig2.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
