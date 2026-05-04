import pandas as pd
import os
import glob
import matplotlib.pyplot as plt

folder_path = r"c:\Users\Administrator\Desktop\python_aspendyn_get_data\csv\acidgas_fm=140"
ss_path = r"c:\Users\Administrator\Desktop\python_aspendyn_get_data\csv\my_own_data\air2(2.94~35.24_110pts)t2(180~200_5pts)acid_gas(135_145_10pts).csv"
plot_dir = os.path.join(folder_path, "plots")

os.makedirs(plot_dir, exist_ok=True)

df_ss = pd.read_csv(ss_path)
df_ss = df_ss[(df_ss['Status'] == 'OK') | (df_ss['Status'].isna())]

files = glob.glob(os.path.join(folder_path, "*_change_*.csv"))

results = []

def lookup_ss(tr2, acidgas, air2):
    df_sub = df_ss.copy()
    closest_t = df_sub.iloc[(df_sub['HEATER2_output_T_SP'] - tr2).abs().argsort()]['HEATER2_output_T_SP'].iloc[0]
    df_sub = df_sub[df_sub['HEATER2_output_T_SP'] == closest_t]
    
    closest_ag = df_sub.iloc[(df_sub['acidgas_Fm'] - acidgas).abs().argsort()]['acidgas_Fm'].iloc[0]
    df_sub = df_sub[df_sub['acidgas_Fm'] == closest_ag]
    
    closest_row = df_sub.iloc[(df_sub['air2_SP_m3'] - air2).abs().argsort()[:1]].iloc[0]
    
    h2s = closest_row.get('B35_H2S')
    so2 = closest_row.get('B35_SO2')
    matched_tr2 = closest_row.get('HEATER2_output_T_SP')
    matched_ag = closest_row.get('acidgas_Fm')
    matched_air2 = closest_row.get('air2_SP_m3')
    
    return h2s, so2, matched_tr2, matched_ag, matched_air2


def sign_str(val):
    if pd.isna(val): return "NaN"
    return "+" if val > 0 else "-" if val < 0 else "0"

for f in files:
    filename = os.path.basename(f)
    if "steady_states" in filename or "all_files" in filename or "comparison" in filename or "air2_180_t2_150_TR2_change_10" in filename or "air2_180_t2_150_air2_change_10" in filename: continue
    
    df_dyn = pd.read_csv(f)
    
    # 抽取動態數據
    df_dyn_before = df_dyn[df_dyn['j'] == 399]
    if df_dyn_before.empty:
        print(f"Skipping {filename} due to missing j==399 row.")
        continue
    
    state_before = df_dyn_before.iloc[0]
    state_after = df_dyn.iloc[-1] 
    
    # 取得 Before 的參數與對應 SS
    tr2_b = state_before.get('HEATER2_output_T_SP')
    ag_b = state_before.get('acidgas_Fm')
    air2_b = state_before.get('air2_SP')
    h2s_dyn_b = state_before.get('B35_H2S')
    so2_dyn_b = state_before.get('B35_SO2')
    h2s_ss_b, so2_ss_b, mt_tr2_b, mt_ag_b, mt_air2_b = lookup_ss(tr2_b, ag_b, air2_b)
    
    # 取得 After 的參數與對應 SS
    tr2_a = state_after.get('HEATER2_output_T_SP')
    ag_a = state_after.get('acidgas_Fm')
    air2_a = state_after.get('air2_SP')
    h2s_dyn_a = state_after.get('B35_H2S')
    so2_dyn_a = state_after.get('B35_SO2')
    h2s_ss_a, so2_ss_a, mt_tr2_a, mt_ag_a, mt_air2_a = lookup_ss(tr2_a, ag_a, air2_a)

    # 計算變化方向 (Gain Direction)
    is_air2_change = "air2_change" in filename
    delta_u = (air2_a - air2_b) if is_air2_change else (tr2_a - tr2_b)
    
    h2s_dyn_gain = (h2s_dyn_a - h2s_dyn_b) / delta_u if delta_u != 0 else 0
    h2s_ss_gain = (h2s_ss_a - h2s_ss_b) / delta_u if delta_u != 0 and pd.notna(h2s_ss_a) and pd.notna(h2s_ss_b) else None
    so2_dyn_gain = (so2_dyn_a - so2_dyn_b) / delta_u if delta_u != 0 else 0
    so2_ss_gain = (so2_ss_a - so2_ss_b) / delta_u if delta_u != 0 and pd.notna(so2_ss_a) and pd.notna(so2_ss_b) else None

    # 判斷是否一致
    h2s_match = "Yes" if pd.notna(h2s_ss_gain) and (h2s_dyn_gain * h2s_ss_gain) > 0 else "No"
    so2_match = "Yes" if pd.notna(so2_ss_gain) and (so2_dyn_gain * so2_ss_gain) > 0 else "No"
    
    # 寫入 CSV 前段紀錄
    results.append({
        'File': filename,
        'State': 'Before Change',
        'Dyn_TR2': tr2_b,
        'Dyn_Air2_SP': air2_b,
        'SS_Matched_TR2': mt_tr2_b,
        'SS_Matched_Air2_m3': mt_air2_b,
        'H2S_Dyn': h2s_dyn_b,
        'H2S_SS': h2s_ss_b,
        'H2S_Diff': h2s_dyn_b - h2s_ss_b if pd.notna(h2s_ss_b) else None,
        'SO2_Dyn': so2_dyn_b,
        'SO2_SS': so2_ss_b,
        'SO2_Diff': so2_dyn_b - so2_ss_b if pd.notna(so2_ss_b) else None,
        'H2S_Gain_Dyn': '', 'H2S_Gain_SS': '', 'H2S_Match': '',
        'SO2_Gain_Dyn': '', 'SO2_Gain_SS': '', 'SO2_Match': ''
    })
    # 寫入 CSV 後段紀錄
    results.append({
        'File': filename,
        'State': 'After Change',
        'Dyn_TR2': tr2_a,
        'Dyn_Air2_SP': air2_a,
        'SS_Matched_TR2': mt_tr2_a,
        'SS_Matched_Air2_m3': mt_air2_a,
        'H2S_Dyn': h2s_dyn_a,
        'H2S_SS': h2s_ss_a,
        'H2S_Diff': h2s_dyn_a - h2s_ss_a if pd.notna(h2s_ss_a) else None,
        'SO2_Dyn': so2_dyn_a,
        'SO2_SS': so2_ss_a,
        'SO2_Diff': so2_dyn_a - so2_ss_a if pd.notna(so2_ss_a) else None,
        'H2S_Gain_Dyn': sign_str(h2s_dyn_gain), 
        'H2S_Gain_SS': sign_str(h2s_ss_gain), 
        'H2S_Match': h2s_match,
        'SO2_Gain_Dyn': sign_str(so2_dyn_gain), 
        'SO2_Gain_SS': sign_str(so2_ss_gain), 
        'SO2_Match': so2_match
    })
    
    # ---------------- 畫圖功能 (藍線 Dynamic vs 紅線 S.S.) ----------------
    j_vals = df_dyn['j']
    h2s_dyn_series = df_dyn.get('B35_H2S')
    so2_dyn_series = df_dyn.get('B35_SO2')
    
    # 防呆檢查確保時間步與靜態匹配皆有數值
    if h2s_dyn_series is not None and so2_dyn_series is not None and pd.notna(h2s_ss_b) and pd.notna(h2s_ss_a):
        h2s_ss_line = [h2s_ss_b if j < 400 else h2s_ss_a for j in j_vals]
        so2_ss_line = [so2_ss_b if j < 400 else so2_ss_a for j in j_vals]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # 在上方繪製 H2S
        ax1.plot(j_vals, h2s_dyn_series, label='Aspen Dynamic', color='blue')
        ax1.plot(j_vals, h2s_ss_line, label='Aspen Plus S.S.', color='red', linestyle='--')
        ax1.axvline(x=400, color='gray', linestyle=':', alpha=0.5, label='Step Change')
        ax1.set_title(f'Dynamic vs Aspen Plus S.S.\n{filename}', fontsize=12)
        ax1.set_ylabel('H2S Mole Fraction', fontsize=11)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 在下方繪製 SO2
        ax2.plot(j_vals, so2_dyn_series, label='Aspen Dynamic', color='blue')
        ax2.plot(j_vals, so2_ss_line, label='Aspen Plus S.S.', color='red', linestyle='--')
        ax2.axvline(x=400, color='gray', linestyle=':', alpha=0.5, label='Step Change')
        ax2.set_ylabel('SO2 Mole Fraction', fontsize=11)
        ax2.set_xlabel('Time Step (j)', fontsize=11)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, f"Combined_{filename.replace('.csv', '.png')}"))
        plt.close()

# 輸出 CSV
df_results = pd.DataFrame(results)
out_csv = os.path.join(folder_path, "comparison_dynamic_vs_ss.csv")
df_results.to_csv(out_csv, index=False)
print("Comparison CSV and plotting are both done!")
print(f"Plots are saved to: {plot_dir}")

# 找出差值最大的條件並印出
print("\n" + "="*60)
print("【相差比例分析報告 (Dynamic vs Steady State)】")

# 找出 H2S 相差比例最大 (排除 SS=0 免除除以零)
valid_h2s = df_results[(df_results['H2S_SS'].notna()) & (df_results['H2S_SS'] != 0)].copy()
if not valid_h2s.empty:
    valid_h2s['H2S_Pct'] = (valid_h2s['H2S_Dyn'] - valid_h2s['H2S_SS']).abs() / valid_h2s['H2S_SS'].abs() * 100
    max_h2s_idx = valid_h2s['H2S_Pct'].idxmax()
    max_h2s_row = valid_h2s.loc[max_h2s_idx]
    print("\n[H2S 誤差比例最巨大的條件]")
    print(f"檔案: {max_h2s_row['File']}")
    print(f"狀態: {max_h2s_row['State']}")
    print(f"Dynamic 取值: {max_h2s_row.get('H2S_Dyn', 0):.6f}  |  SS 取值: {max_h2s_row.get('H2S_SS', 0):.6f}")
    print(f"最大相差比例: {max_h2s_row['H2S_Pct']:.2f}%")

# 找出 SO2 相差比例最大 (排除 SS=0 免除除以零)
valid_so2 = df_results[(df_results['SO2_SS'].notna()) & (df_results['SO2_SS'] != 0)].copy()
if not valid_so2.empty:
    valid_so2['SO2_Pct'] = (valid_so2['SO2_Dyn'] - valid_so2['SO2_SS']).abs() / valid_so2['SO2_SS'].abs() * 100
    max_so2_idx = valid_so2['SO2_Pct'].idxmax()
    max_so2_row = valid_so2.loc[max_so2_idx]
    print("\n[SO2 誤差比例最巨大的條件]")
    print(f"檔案: {max_so2_row['File']}")
    print(f"狀態: {max_so2_row['State']}")
    print(f"Dynamic 取值: {max_so2_row.get('SO2_Dyn', 0):.6f}  |  SS 取值: {max_so2_row.get('SO2_SS', 0):.6f}")
    print(f"最大相差比例: {max_so2_row['SO2_Pct']:.2f}%")
print("="*60 + "\n")
