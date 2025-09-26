import claus_plant_flow_record as plant  #環境-(Aspen)
import numpy as np
import pandas as pd

import os

###############################  Model setting  ####################################
PROJECT_NAME = 'Test'
OUTPUT_FILE = 'Test'
dt = 1  #每一步的模擬時間(MIN)
MAX_EP_STEPS = 1440 #每個訓練及的最大步數
MAX_EPISODES = 10

env = plant.Env(dt, MAX_EP_STEPS) #參數給到環境中

datacomp = np.zeros((MAX_EPISODES*MAX_EP_STEPS, 8))
data = np.zeros((MAX_EPISODES*MAX_EP_STEPS, 77))
index_columns = ['i', 'j', 'steps', 'acidgas_Fm', 'acidgas_CO2', 'acidgas_H2O', 'acidgas_H2S', 'acidgas_T', 'acidgas_P','air','air_SP',
                 'second_air2', 'air2_SP', 'COG', 'COG_SP', 'burner_input_T_SP', 'burner_input_T_PV', 'burner_inputP', 'burner_output_T_SP', 'burner_output_T_PV', 'burner_output_P_SP', 'burner_output_P_PV',
                 'fur_F', 'fur_inputT', 'fur_inputP', 'fur_temp', 'fur_outputT', 'fur_outputP_SP', 'fur_outputP_PV',
                 'WHB_F', 'WHB_inputT', 'WHB_inputP', 'WHB_outputT', 'WHB_outputP',
                 'SEP1_F', 'SEP1_P_SP', 'SEP1_P_PV', 'SEP1_T',
                 'HEATER1_F', 'HEATER1_input_T', 'HEATER1_input_P', 'HEATER1_output_T_SP', 'HEATER1_output_T_PV', 'HEATER1_output_P',
                 'cat1_F', 'cat1_input_temp', 'cat1_output_temp', 'cat1_input_P', 'cat1_output_P_SP', 'cat1_output_P_PV', 'cat1_deltaP',
                 'SEP2_F', 'SEP2_P_SP', 'SEP2_P_PV', 'SEP2_T',
                 'HEATER2_F','HEATER2_input_T', 'HEATER2_input_P', 'HEATER2_output_T_SP', 'HEATER2_output_T_PV', 'HEATER2_output_P',
                 'cat2_F', 'cat2_input_temp', 'cat2_output_temp', 'cat2_input_P', 'cat2_output_P_SP', 'cat2_output_P_PV', 'cat2_deltaP',
                 'SEP3_F', 'SEP3_P_SP', 'SEP3_P_PV', 'SEP3_T', 'B35_H2S', 'B35_SO2', 'ratio', 'ratioSP','conv']
data_df = pd.DataFrame(np.zeros((MAX_EPISODES*MAX_EP_STEPS, 77)), columns=index_columns)

def save_result(data, datacomp, episode, steps):
    data[(episode) * MAX_EP_STEPS + steps, 0] = episode
    data[(episode) * MAX_EP_STEPS + steps, 1] = steps
    data[(episode) * MAX_EP_STEPS + steps, 2] = episode * MAX_EP_STEPS + steps
    data[(episode) * MAX_EP_STEPS + steps, 3:77] = env.data_conclusion()  # 第二欄開始

    datacomp[(episode) * MAX_EP_STEPS + steps, 0] = episode
    datacomp[(episode) * MAX_EP_STEPS + steps, 1] = steps
    datacomp[(episode) * MAX_EP_STEPS + steps, 2:8] = env.data_conclusion2()
    return data, datacomp

################################## Training #####################################################
for i in range(MAX_EPISODES):#每個EPISODES MAX_EPISODES步，一次MAX_EPISODES分鐘
    state = env.reset()   #環境中抓出最初始步驟，有用到再來抓

    if i < 11:
        for j in range(MAX_EP_STEPS):
            print(f"j={j},i={i}")
            y_ = env.step(j, i, 1)
            z_ = env.step_air2_T(j, i)
            env.do_dis3(*y_, *z_)
            env.run_step(j, i)
            save_result(data, datacomp, i, j)

            data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
            # 将所有列作为索引
            # data_df.set_index(index_columns, inplace=True)
            # 保存为 CSV 文件
            os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
            data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
        data_df.to_csv('csv/%s/day/%s_dataform%d.csv' % (PROJECT_NAME, OUTPUT_FILE, i))

    # elif 1 <= i < 2:
    #     for j in range(MAX_EP_STEPS):
    #
    #         print(f"j={j},i={i}")
    #         y_ = env.step(j, i, 1)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[( i ) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
    #
    #     data_df.to_csv('csv/%s/day/%s_dataform%d.csv' % (PROJECT_NAME, OUTPUT_FILE, i))
    #
    # elif 2 <= i < 3 :
    #     for j in range(MAX_EP_STEPS):
    #         print(f"j={j},i={i}")
    #         y_ = env.step3(j, i, 1, 1.2, MAX_EP_STEPS)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
    #     data_df.to_csv('csv/%s/day/%s_dataform%d.csv' % (PROJECT_NAME, OUTPUT_FILE, i))
    #
    # elif 3 <= i < 8:
    #     for j in range(MAX_EP_STEPS):
    #         print(f"j={j},i={i}")
    #         y_ = env.step(j, i, 1.2)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
    #     data_df.to_csv('csv/%s/day/%s_dataform%d.csv' % (PROJECT_NAME, OUTPUT_FILE, i))
    #
    # elif 8 <= i < 9:
    #     for j in range(MAX_EP_STEPS):
    #         print(f"j={j},i={i}")
    #         y_ = env.step3(j, i, 1.2, 1, MAX_EP_STEPS)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
    #     data_df.to_csv('csv/%s/day/%s_dataform%d.csv' % (PROJECT_NAME, OUTPUT_FILE, i))
    #
    # elif 9 <= i < 14:
    #     for j in range(MAX_EP_STEPS):
    #         print(f"j={j},i={i}")
    #         y_ = env.step(j, i, 1)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
    #
    # elif 14 <= i < 15:
    #     for j in range(MAX_EP_STEPS):
    #         print(f"j={j},i={i}")
    #         y_ = env.step3(j, i, 1, 0.8, MAX_EP_STEPS)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
    #
    # elif 15 <= i < 16:
    #     for j in range(MAX_EP_STEPS):
    #         print(f"j={j},i={i}")
    #         y_ = env.step(j, i, 0.8)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
    #
    #
    # elif 16 <= i < 17:
    #     for j in range(MAX_EP_STEPS):
    #         print(f"j={j},i={i}")
    #         y_ = env.step3(j, i, 0.8, 1, MAX_EP_STEPS)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
    #
    # else:
    #     for j in range(MAX_EP_STEPS):
    #         print(f"j={j},i={i}")
    #         y_ = env.step(j, i, 1)
    #         z_ = env.step_ratio_T(j, i)
    #         env.do_dis3(*y_, *z_)
    #         env.run_step(j, i)
    #         save_result(data, datacomp, i, j)
    #
    #         data_df.iloc[(i) * MAX_EP_STEPS + j] = np.array(data[(i) * MAX_EP_STEPS + j, :]).reshape(-1)  # 创建 DataFrame 并指定列名
    #         # 将所有列作为索引
    #         # data_df.set_index(index_columns, inplace=True)
    #         # 保存为 CSV 文件
    #         os.makedirs('csv/%s' % PROJECT_NAME, exist_ok=True)
    #         data_df.to_csv('csv/%s/%s_dataform.csv' % (PROJECT_NAME, OUTPUT_FILE))
