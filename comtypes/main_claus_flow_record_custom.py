import atexit
import glob
import os

import numpy as np
import pandas as pd

import claus_plant_flow_record_custom as plant


PROJECT_NAME = "out_of_distribution"
OUTPUT_FILE = "out_of_distribution"
ASPEN_FILE_NAME = "claus OK1heaterdis1H2Sincrease try9-2_NEW_ss.dynf"
dt = 1
MAX_EP_STEPS = int(os.environ.get("CLAUS_MAX_EP_STEPS", "1440"))
MAX_EPISODES = int(os.environ.get("CLAUS_MAX_EPISODES", "5"))
FULL_DATA_FILE_ROWS = int(
    os.environ.get("CLAUS_FULL_DATA_FILE_ROWS", str(5 * 1440))
)
SYNC_STEPS = os.environ.get("CLAUS_SYNC_STEPS", "Full")
RECORD_HISTORY = os.environ.get("CLAUS_RECORD_HISTORY", "1").lower() not in {
    "0",
    "false",
    "no",
}
BATCH_COM_MODE = os.environ.get("CLAUS_BATCH_COM", "off").lower()


def csv_data_row_count(file_name):
    with open(file_name, encoding="utf-8", newline="") as csv_file:
        return max(sum(1 for _ in csv_file) - 1, 0)

csv_dir = os.path.join("csv", PROJECT_NAME)
day_dir = os.path.join(csv_dir, "day")
os.makedirs(csv_dir, exist_ok=True)
os.makedirs(day_dir, exist_ok=True)

existing_files = glob.glob(
    os.path.join(csv_dir, f"{OUTPUT_FILE}_dataform_*.csv")
)
file_indices = []
for file_name in existing_files:
    try:
        index_text = file_name.split(f"{OUTPUT_FILE}_dataform_")[-1].split(".csv")[0]
        file_indices.append(int(index_text))
    except ValueError:
        pass
next_idx = max(file_indices) + 1 if file_indices else 1
completed_full_file_count = sum(
    csv_data_row_count(file_name) == FULL_DATA_FILE_ROWS
    for file_name in existing_files
)
tr2_mean = plant.tr2_mean_for_completed_files(completed_full_file_count)
print(
    f"Completed full data files: {completed_full_file_count}; "
    f"TR2 Gaussian mean for this file: {tr2_mean}"
)

env = plant.Env(
    dt,
    MAX_EP_STEPS,
    ASPEN_FILE_NAME,
    tr2_mean=tr2_mean,
    sync_steps=SYNC_STEPS,
    record_history=RECORD_HISTORY,
    batch_com_mode=BATCH_COM_MODE,
)
atexit.register(env.close)

data = np.zeros((MAX_EPISODES * MAX_EP_STEPS, 78))
index_columns = [
    "i",
    "j",
    "steps",
    "acidgas_Fm",
    "acidgas_Fv",
    "acidgas_CO2",
    "acidgas_H2O",
    "acidgas_H2S",
    "acidgas_T",
    "acidgas_P",
    "air",
    "air_SP",
    "second_air2",
    "air2_SP",
    "COG",
    "COG_SP",
    "burner_input_T_SP",
    "burner_input_T_PV",
    "burner_inputP",
    "burner_output_T_SP",
    "burner_output_T_PV",
    "burner_output_P_SP",
    "burner_output_P_PV",
    "fur_F",
    "fur_inputT",
    "fur_inputP",
    "fur_temp",
    "fur_outputT",
    "fur_outputP_SP",
    "fur_outputP_PV",
    "WHB_F",
    "WHB_inputT",
    "WHB_inputP",
    "WHB_outputT",
    "WHB_outputP",
    "SEP1_F",
    "SEP1_P_SP",
    "SEP1_P_PV",
    "SEP1_T",
    "HEATER1_F",
    "HEATER1_input_T",
    "HEATER1_input_P",
    "HEATER1_output_T_SP",
    "HEATER1_output_T_PV",
    "HEATER1_output_P",
    "cat1_F",
    "cat1_input_temp",
    "cat1_output_temp",
    "cat1_input_P",
    "cat1_output_P_SP",
    "cat1_output_P_PV",
    "cat1_deltaP",
    "SEP2_F",
    "SEP2_P_SP",
    "SEP2_P_PV",
    "SEP2_T",
    "HEATER2_F",
    "HEATER2_input_T",
    "HEATER2_input_P",
    "HEATER2_output_T_SP",
    "HEATER2_output_T_PV",
    "HEATER2_output_P",
    "cat2_F",
    "cat2_input_temp",
    "cat2_output_temp",
    "cat2_input_P",
    "cat2_output_P_SP",
    "cat2_output_P_PV",
    "cat2_deltaP",
    "SEP3_F",
    "SEP3_P_SP",
    "SEP3_P_PV",
    "SEP3_T",
    "B35_H2S",
    "B35_SO2",
    "ratio",
    "ratioSP",
    "conv",
]
data_df = pd.DataFrame(
    np.zeros((MAX_EPISODES * MAX_EP_STEPS, 78)), columns=index_columns
)


def save_result(data, episode, steps):
    row = episode * MAX_EP_STEPS + steps
    data[row, 0] = episode
    data[row, 1] = steps
    data[row, 2] = row
    data[row, 3:78] = env.data_conclusion()

    return data


output_path = os.path.join(csv_dir, f"{OUTPUT_FILE}_dataform_{next_idx}.csv")
with open(output_path, "w", encoding="utf-8", newline="") as output_csv:
    for i in range(MAX_EPISODES):
        state = env.reset()
        if i >= 11:
            continue

        for j in range(MAX_EP_STEPS):
            print(f"j={j},i={i}")
            inlet_values = env.step(j, i, 1)
            control_values = env.step_air2_T(j, i)
            env.do_dis3(*inlet_values, *control_values)
            env.run_step(j, i)
            save_result(data, i, j)

            row = i * MAX_EP_STEPS + j
            data_df.iloc[row] = data[row].reshape(-1)
            data_df.iloc[[row]].to_csv(output_csv, header=(row == 0))
            output_csv.flush()

        data_df.to_csv(os.path.join(day_dir, f"{OUTPUT_FILE}_dataform{i}.csv"))

atexit.unregister(env.close)
env.close()
