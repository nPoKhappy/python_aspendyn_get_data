import win32com.client
import numpy as np
import random

class Env(object):
    def __init__(self, dt, MAX_EP_STEPS):
        # dt:每一步的模擬時間
        # max_ep_steps: 每個訓練及的最大步數

        ##############  Aspen啟用  ######################################
        # 嘗試不同的 COM 程式 ID
        com_ids = ['AD Application', 'AspenModeler.Application', 'AspenModeler']
        self.adyn = None
        
        for com_id in com_ids:
            try:
                print(f"嘗試連接 COM ID: {com_id}")
                self.adyn = win32com.client.Dispatch(com_id)
                print(f"成功連接到: {com_id}")
                break
            except Exception as e:
                print(f"連接 {com_id} 失敗: {e}")
                continue
        
        if self.adyn is None:
            raise Exception("無法連接到任何 Aspen COM 接口")
            
        self.adyn.Visible = True  #Aspen視窗的可視化
        
        # 檢查 COM 物件的方法
        print("可用的方法:")
        try:
            all_methods = [method for method in dir(self.adyn) if not method.startswith('_')]
            for method in all_methods:
                if any(keyword in method.lower() for keyword in ['open', 'document', 'file', 'load']):
                    print(f"  - {method}")
            print("所有方法:")
            print(all_methods[:20])  # 顯示前20個方法
        except:
            pass
        
        import os
        # 取得絕對路徑
        current_dir = os.path.dirname(os.path.abspath(__file__))
        aspen_file_path = os.path.join(current_dir, "ASPen_file", "claus OK1heaterdis1H2Sincrease try9-2.dynf")
        
        print(f"嘗試開啟檔案: {aspen_file_path}")
        print(f"檔案是否存在: {os.path.exists(aspen_file_path)}")
        
        # 嘗試使用不同的 COM 方法
        file_opened = False
        
        # 方法列表，按照可能性排序
        methods_to_try = [
            ("Application.OpenDocument", lambda path: self.adyn.Application.OpenDocument(path)),
            ("Open", lambda path: self.adyn.Open(path)),
            ("LoadFromFile", lambda path: self.adyn.LoadFromFile(path)),
            ("Document.Open", lambda path: self.adyn.Document.Open(path)),
            ("FileOpen", lambda path: self.adyn.FileOpen(path)),
            ("OpenFile", lambda path: self.adyn.OpenFile(path)),
        ]
        
        for method_name, method_func in methods_to_try:
            if file_opened:
                break
                
            try:
                print(f"嘗試方法: {method_name}")
                method_func(aspen_file_path)
                print(f"成功使用 {method_name} 開啟檔案")
                file_opened = True
            except AttributeError as e:
                print(f"  {method_name} 方法不存在: {e}")
            except Exception as e:
                print(f"  {method_name} 失敗: {e}")
        
        # 如果上述方法都不行，嘗試直接調用 COM 方法
        if not file_opened:
            try:
                print("嘗試直接呼叫 Invoke 方法")
                # 有時候需要直接使用低階的 COM 方法
                result = self.adyn._oleobj_.Invoke(0x60020000, 0, 1, 1, aspen_file_path)
                print("直接 Invoke 成功")
                file_opened = True
            except Exception as e:
                print(f"直接 Invoke 失敗: {e}")
        
        if not file_opened:
            print("\n所有自動開啟方法都失敗。")
            print("請手動在 Aspen Dynamics 中開啟以下檔案:")
            print(f"  {aspen_file_path}")
            print("開啟後請按 Enter 鍵繼續...")
            input("等待手動開啟檔案...")
            
            # 嘗試獲取已開啟的文檔
            try:
                if hasattr(self.adyn, 'ActiveDocument'):
                    if self.adyn.ActiveDocument is not None:
                        print("檢測到已開啟的文檔")
                        file_opened = True
                elif hasattr(self.adyn, 'Documents'):
                    if self.adyn.Documents.Count > 0:
                        print("檢測到已開啟的文檔")
                        file_opened = True
            except:
                pass
            
            if not file_opened:
                raise Exception("無法檢測到已開啟的檔案。請確認檔案已正確開啟。")
        
        self.sim = self.adyn.Simulation
        self.sim.options.TimeSettings.RecordHistory = True #記錄所有變數的歷史數值
        self.fsheet = self.sim.Flowsheet
        self.streams = self.fsheet.Streams
        self.blocks = self.fsheet.Blocks

        self.dt = dt
        self.max_ep_step = MAX_EP_STEPS
        self.inlet_count = 0
    #讀資料
    def get_input_composition(self): #獲取進料資訊
        acidgas_Fm = self.streams('ACIDGAS').F.value
        acidgas_CO2 = self.streams('ACIDGAS').Fcn('CO2').value
        acidgas_H2O = self.streams('ACIDGAS').Fcn('H2O').value
        acidgas_H2S = self.streams('ACIDGAS').Fcn('H2S').value
        acidgas_T = self.streams('ACIDGAS').T.value
        acidgas_P = self.streams('ACIDGAS').P.value
        air = self.streams('AIR').F.value
        air_SP = self.blocks('B17').SP.value
        return acidgas_Fm, acidgas_CO2, acidgas_H2O, acidgas_H2S, acidgas_T, acidgas_P, air, air_SP

    def input_composition_compare(self): #獲取進料資訊
        FcR_acidgas_CO2 = self.streams('ACIDGAS').FcR('CO2').value
        FcR_acidgas_H2O = self.streams('ACIDGAS').FcR('H2O').value
        FcR_acidgas_H2S = self.streams('ACIDGAS').FcR('H2S').value
        acidgas_CO2 = self.streams('ACIDGAS').Fcn('CO2').value
        acidgas_H2O = self.streams('ACIDGAS').Fcn('H2O').value
        acidgas_H2S = self.streams('ACIDGAS').Fcn('H2S').value
        return FcR_acidgas_CO2, FcR_acidgas_H2O, FcR_acidgas_H2S, acidgas_CO2, acidgas_H2O, acidgas_H2S

    def get_burner_composition(self):  # 獲取鍋爐資訊

        second_air2 = self.streams('AIR2').Fv.value
        air2_SP = self.blocks('B33').SP.value
        COG = self.streams('S4').Fv.value
        # COG_SP =self.streams('S4').F.value
        COG_SP = self.blocks('B35').SP.value
        burner_input_T_SP = self.blocks('B18').SP.value
        burner_input_T_PV = self.blocks('B18').PV.value
        burner_inputP = self.streams('S8').P.value
        burner_output_T_SP = self.blocks('B19').SP.value
        burner_output_T_PV = self.blocks('B19').PV.value
        burner_output_P_SP = self.blocks('BURNER_PC').SP.value
        burner_output_P_PV = self.blocks('BURNER_PC').PV.value
        return second_air2, air2_SP, COG, COG_SP, burner_input_T_SP, burner_input_T_PV, burner_inputP, burner_output_T_SP, burner_output_T_PV, burner_output_P_SP, burner_output_P_PV

    def get_furance_composition(self): #獲取鍋爐資訊
        fur_F = self.streams('S12').F.value
        fur_inputT = self.blocks('FURANCE').T(0).value
        fur_inputP = self.streams('S12').P.value
        fur_temp = self.blocks('FURANCE').T(1).value
        fur_outputT = self.streams('S15').T.value
        fur_outputP_SP = self.blocks('FURANCE_PC').SP.value
        fur_outputP_PV = self.blocks('FURANCE_PC').PV.value

        return fur_F, fur_inputT, fur_inputP, fur_temp, fur_outputT, fur_outputP_SP, fur_outputP_PV

    def get_WHB_composition(self): #獲取鍋爐資訊
        WHB_F = self.streams('S16').F.value
        WHB_inputT = self.streams('S16').T.value
        WHB_inputP = self.streams('S16').P.value
        WHB_outputT = self.streams('S13').T.value
        WHB_outputP = self.streams('S13').P.value
        return WHB_F, WHB_inputT, WHB_inputP, WHB_outputT, WHB_outputP

    def get_SEP1_composition(self):
        SEP1_F = self.streams('S14').F.value
        SEP1_P_SP = self.blocks('SEP1_PC').SP.value
        SEP1_P_PV = self.blocks('SEP1_PC').PV.value
        SEP1_T = self.blocks('SEP1').T.value

        return SEP1_F, SEP1_P_SP, SEP1_P_PV, SEP1_T

    def get_HEATER1_composition(self):
        HEATER1_F = self.streams('S36').F.value
        HEATER1_input_T = self.streams('S36').T.value
        HEATER1_input_P = self.streams('S36').P.value
        HEATER1_output_T_SP = self.blocks('B21').SP.value
        HEATER1_output_T_PV = self.blocks('B21').PV.value
        HEATER1_output_P = self.streams('S20').P.value
        return HEATER1_F, HEATER1_input_T, HEATER1_input_P, HEATER1_output_T_SP, HEATER1_output_T_PV, HEATER1_output_P

    def get_cat1_composition(self): #獲取觸媒1資訊
        cat1_F = self.streams('S21').F.value
        cat1_input_temp = self.streams('S21').T.value
        cat1_output_temp = self.streams('S22').T.value
        cat1_input_P = self.streams('S21').P.value
        cat1_output_P_SP = self.blocks('CAT1_PC').SP.value
        cat1_output_P_PV = self.blocks('CAT1_PC').PV.value
        cat1_deltaP = abs(cat1_input_P-cat1_output_P_PV)*1000  # 壓力差(bar)*1000(minibar)
        return cat1_F, cat1_input_temp, cat1_output_temp, cat1_input_P, cat1_output_P_SP, cat1_output_P_PV, cat1_deltaP

    def get_SEP2_composition(self):
        SEP2_F = self.streams('S23').F.value
        SEP2_P_SP = self.blocks('SEP2_PC').SP.value
        SEP2_P_PV = self.blocks('SEP2_PC').PV.value
        SEP2_T = self.blocks('SEP2').T.value

        return SEP2_F, SEP2_P_SP, SEP2_P_PV, SEP2_T

    def get_HEATER2_composition(self):
        HEATER2_F = self.streams('S25').F.value
        HEATER2_input_T = self.streams('S25').T.value
        HEATER2_input_P = self.streams('S25').P.value
        HEATER2_output_T_SP = self.blocks('B20').SP.value
        HEATER2_output_T_PV = self.blocks('B20').PV.value
        HEATER2_output_P = self.streams('S20').P.value
        return HEATER2_F, HEATER2_input_T, HEATER2_input_P, HEATER2_output_T_SP, HEATER2_output_T_PV, HEATER2_output_P

    def get_cat2_composition(self):  # 獲取觸媒2資訊
        cat2_F = self.streams('S27').F.value
        cat2_input_temp = self.streams('S27').T.value
        cat2_output_temp = self.streams('S28').T.value
        cat2_input_P = self.streams('S27').P.value
        cat2_output_P_SP = self.blocks('CAT2_PC').SP.value
        cat2_output_P_PV = self.blocks('CAT2_PC').PV.value
        cat2_deltaP = abs(cat2_input_P - cat2_output_P_PV) * 1000  # 壓力差(bar)*1000(minibar)
        return cat2_F, cat2_input_temp, cat2_output_temp, cat2_input_P, cat2_output_P_SP, cat2_output_P_PV, cat2_deltaP

    def get_SEP3_composition(self):
        SEP3_F = self.streams('S29').F.value
        SEP3_P_SP = self.blocks('SEP3_PC').SP.value
        SEP3_P_PV = self.blocks('SEP3_PC').PV.value
        SEP3_T = self.blocks('SEP3').T.value

        return SEP3_F, SEP3_P_SP, SEP3_P_PV, SEP3_T

    def get_composition(self):  # 獲取S33出料濃度資訊
        B35_H2S = self.streams('S33').Zn('H2S').value
        B35_SO2 = self.streams('S33').Zn('SO2').value
        H2S_flowrate = self.streams('S33').Fcn('H2S').value
        SO2_flowrate = self.streams('S33').Fcn('SO2').value
        acidgas_H2S = self.streams('ACIDGAS').Fcn('H2S').value
        conv= (acidgas_H2S-H2S_flowrate-SO2_flowrate)/acidgas_H2S
        ratio = B35_H2S / B35_SO2
        ratioSP = self.blocks('B23').SPRemote().value
        return B35_H2S, B35_SO2, ratio, ratioSP, conv

    def data_conclusion(self):

        data0, data1, data2, data3, data4, data5, data6, data73 = self.get_input_composition()
        data0 = np.array([data0])
        data1 = np.array([data1])
        data2 = np.array([data2])
        data3 = np.array([data3])
        data4 = np.array([data4])
        data5 = np.array([data5])
        data6 = np.array([data6])
        data73 = np.array([data73])

        print("inlet_F=", data0)
        print("mole_flowCO2=", data1)
        print("mole_flowH2O=", data2)
        print("mole_flowH2S=", data3)

        data7, data74, data8, data75, data9, data10, data11, data12, data13, data14, data15 = self.get_burner_composition()
        data7 = np.array([data7])
        data74 = np.array([data74])
        data8 = np.array([data8])
        data75 = np.array([data75])
        data9 = np.array([data9])
        data10 = np.array([data10])
        data11 = np.array([data11])
        data12 = np.array([data12])
        data13 = np.array([data13])
        data14 = np.array([data14])
        data15 = np.array([data15])

        data16, data17, data18, data19, data20, data21, data22 = self.get_furance_composition()
        data16 = np.array([data16])
        data17 = np.array([data17])
        data18 = np.array([data18])
        data19 = np.array([data19])
        data20 = np.array([data20])
        data21 = np.array([data21])
        data22 = np.array([data22])

        data23, data24, data25, data26, data27 = self.get_WHB_composition()
        data23 = np.array([data23])
        data24 = np.array([data24])
        data25 = np.array([data25])
        data26 = np.array([data26])
        data27 = np.array([data27])

        data28, data29, data30, data31= self.get_SEP1_composition()

        data28 = np.array([data28])
        data29 = np.array([data29])
        data30 = np.array([data30])
        data31 = np.array([data31])

        data32, data33, data34, data35, data36, data37 = self.get_HEATER1_composition()

        data32 = np.array([data32])
        data33 = np.array([data33])
        data34 = np.array([data34])
        data35 = np.array([data35])
        data36 = np.array([data36])
        data37 = np.array([data37])

        data38, data39, data40, data41, data42, data43, data44, = self.get_cat1_composition()


        data38 = np.array([data38])
        data39 = np.array([data39])
        data40 = np.array([data40])
        data41 = np.array([data41])
        data42 = np.array([data42])
        data43 = np.array([data43])
        data44 = np.array([data44])

        data45, data46, data47, data48 = self.get_SEP2_composition()

        data45 = np.array([data45])
        data46 = np.array([data46])
        data47 = np.array([data47])
        data48 = np.array([data48])

        data49, data50, data51,  data52, data53, data54 = self.get_HEATER2_composition()

        data49 = np.array([data49])
        data50 = np.array([data50])
        data51 = np.array([data51])
        data52 = np.array([data52])
        data53 = np.array([data53])
        data54 = np.array([data54])

        data55, data56, data57, data58, data59, data60, data61 = self.get_cat2_composition()

        data55 = np.array([data55])
        data56 = np.array([data56])
        data57 = np.array([data57])
        data58 = np.array([data58])
        data59 = np.array([data59])
        data60 = np.array([data60])
        data61 = np.array([data61])

        data62, data63, data64, data65 = self.get_SEP3_composition()

        data62 = np.array([data62])
        data63 = np.array([data63])
        data64 = np.array([data64])
        data65 = np.array([data65])

        data66, data67, data68, data69, data76= self.get_composition()

        data66 = np.array([data66])
        data67 = np.array([data67])
        data68 = np.array([data68])
        data69 = np.array([data69])
        data76 = np.array([data76])
        print("conv=",data76)
        return np.concatenate([data0, data1, data2, data3, data4, data5, data6, data73, data7, data74, data8, data75, data9, data10, data11, data12, data13, data14, data15, data16, data17, data18, data19, data20, data21, data22, data23, data24, data25, data26, data27, data28, data29, data30, data31, data32, data33, data34, data35, data36, data37, data38, data39, data40, data41, data42, data43, data44, data45, data46, data47, data48, data49, data50, data51, data52, data53, data54, data55, data56, data57, data58, data59, data60, data61, data62, data63, data64, data65, data66, data67, data68, data69, data76])

    def data_conclusion2(self):
        data67, data68, data69, data70, data71, data72 = self.input_composition_compare()
        data67 = np.array([data67])
        data68 = np.array([data68])
        data69 = np.array([data69])
        data70 = np.array([data70])
        data71 = np.array([data71])
        data72 = np.array([data72])
        return np.concatenate([data67, data68, data69, data70, data71, data72])
    def reset(self):
        bB35_SO2, bB35_H2S, ratio, ratioSP,conv = self.get_composition() #取得目前出口濃度資訊(初始狀態)
        return np.array([bB35_SO2, bB35_H2S, ratio, ratioSP,conv])  #回傳到main，看模型是否需要初始狀態



    def step(self, steps, episodes, ram): #模型控制動作給到step環境中
        #####inlet_disturbance##########
        self.dis(ram)  #進料組成改變(給值)
        # self.dis2(ram)  #進料組成改變(給值)
        return self.Fn_carbon_dioxide, self.Fn_hydrogen_dioxide, self.Fn_hydrogen_sulfide, self.inlet_T, self.inlet_P


        ################################ 動作執行 ################################


    def dis(self, ram):      #多少步之後重新模擬進料組成
        if self.inlet_count % 10 == 0: #每 10*1 min 改變進料組成及狀態
            self.Fn_carbon_dioxide, self.Fn_hydrogen_dioxide, self.Fn_hydrogen_sulfide, self.inlet_T, self.inlet_P= self.disturbance(ram) #物流進料擾動生成
            self.inlet_count += 1
        else:
            self.inlet_count += 1

    def disturbance(self, ram):        #gauss random disturbance
        # 每個組成在各自範圍內random出各自的莫耳流率
        # Fn_carbon_dioxide = self.streams('ACIDGAS').FcR('CO2').value   # 莫爾流率
        # Fn_hydrogen_dioxide = self.streams('ACIDGAS').FcR('H2O').value
        # Fn_hydrogen_sulfide = self.streams('ACIDGAS').FcR('H2S').value
        # Fn_carbon_dioxide = Fn_carbon_dioxide + random.gauss(0, 1.023)  # 莫爾流率
        # Fn_hydrogen_dioxide = Fn_hydrogen_dioxide + random.gauss(0, 1.158)
        # Fn_hydrogen_sulfide = Fn_hydrogen_sulfide + random.gauss(0, 1.38)
        Fn_carbon_dioxide = random.gauss(40.1268, 1.023)  # 莫爾流率
        Fn_hydrogen_dioxide = random.gauss(45.3971, 1.158)
        Fn_hydrogen_sulfide = random.gauss(54.9391, 1.38)
        inlet_T = random.gauss(83.6, 0.4265)
        inlet_P = random.gauss(1.5722+(0.1*ram**2), 0.0085)
        # inlet_T = random.gauss(83.6, 0)
        # inlet_P = random.gauss(1.5722+(0.1*ram**2), 0)
        # TR1 = random.gauss(234.137, 1.194)
        return Fn_carbon_dioxide, Fn_hydrogen_dioxide, Fn_hydrogen_sulfide, inlet_T,  inlet_P


    def do_dis3(self, A,B,C, inlet_T, inlet_P, TR1, TR2, air2):
        #mole_flow: 物流各項進料的莫耳流率組成
        #inlet_T: 物流進料溫度  inlet_P:  物流進料壓力
        self.streams('ACIDGAS').FcR('CO2').Value = A #莫爾流率
        self.streams('ACIDGAS').FcR('H2O').Value = B
        self.streams('ACIDGAS').FcR('H2S').Value = C
        self.streams('ACIDGAS').T.value = inlet_T
        self.streams('ACIDGAS').P.value = inlet_P
        self.blocks('B21').SPRemote().value = TR1
        self.blocks('B20').SPRemote().value = TR2
        self.blocks('B33').SPRemote().value = air2
        print("inlet_T", inlet_T)
        print("inlet_P", inlet_P)
        return A, B, C, inlet_T, inlet_P, TR1, TR2, air2

    def step_air2_T(self, steps, episodes):  # 模型控制動作給到step環境中
        #####inlet_disturbance##########
        # T2, air2 = self.disturbance_air2_T(steps)  # 進料組成改變(給值)
        # return T2, air2
        self.TR1,self.TR2, self.air2 = self.disturbance_air2_T(steps)
        return self.TR1, self.TR2, self.air2
        ################################ 動作執行 ################################
        # self.run_step(steps, episodes)  # 輸入暫停時間並執行動作



    def disturbance_air2_T(self, steps): #gauss random disturbance
        dead_time = 10
        ramping_time = 300
        manual_time = 480
        if steps == 0:

            self.op_TR1,self.op_TR2, self.op_air2 = self.op(manual_time)
            self.deadtime_TR1,self.deadtime_TR2, self.deadtime_air2 = self.deadtime_SPRemote()
        n = steps % manual_time
        stage = int(steps / manual_time)
        if n < (dead_time + ramping_time):
            if n < dead_time:
                TR1 = self.blocks('B21').SPRemote().value
                TR2 = self.blocks('B20').SPRemote().value
                air2 = self.blocks('B33').SPRemote().value
            else:
                if stage == 0:
                    ramp_TR1 = np.linspace(self.deadtime_TR1, self.op_TR1[stage], ramping_time)
                    ramp_TR2 = np.linspace(self.deadtime_TR2, self.op_TR2[stage], ramping_time)
                    ramp_air2 = np.linspace(self.deadtime_air2, self.op_air2[stage], ramping_time)
                else:
                    ramp_TR1 = np.linspace(self.op_TR1[stage-1], self.op_TR1[stage], ramping_time)
                    ramp_TR2 = np.linspace(self.op_TR2[stage-1], self.op_TR2[stage], ramping_time)
                    ramp_air2 = np.linspace(self.op_air2[stage-1], self.op_air2[stage], ramping_time)
                TR1 = ramp_TR1[range(ramping_time)[(steps % manual_time) - dead_time]]
                TR2 = ramp_TR2[range(ramping_time)[(steps % manual_time) - dead_time]]
                air2 = ramp_air2[range(ramping_time)[(steps % manual_time) - dead_time]]

        else:
            TR1 = self.op_TR1[stage]
            TR2 = self.op_TR2[stage]
            air2 = self.op_air2[stage]
        print('TR1=', TR1)
        print('TR2=', TR2)
        print('air2=', air2)
        return TR1, TR2, air2

    def op(self, manual_time):
        op_TR1 = [random.gauss(250, 25) for _ in range(int(60 * 24 / manual_time))]
        op_TR2 = [random.gauss(180, 15) for _ in range(int(60 * 24 / manual_time))]  # 创建一个名为 op_TR2 的列表，以 manual_time 为时间间隔所能生成的随机高斯分布的值的个数。
        # op_TR2 = [random.gauss(180, 0) for _ in range(int(60 * 24 / manual_time))]  # 创建一个名为 op_TR2 的列表，以 manual_time 为时间间隔所能生成的随机高斯分布的值的个数。
        print('op_TR1=', op_TR1)
        op_air2 = [random.gauss(220, 50) for _ in range(int(60 * 24 / manual_time))]
        print('op_TR2=', op_TR2)
        print('op_air2=', op_air2)
        return op_TR1, op_TR2, op_air2

    def deadtime_SPRemote(self):
        deadtime_TR1 = self.blocks('B21').SPRemote().value
        deadtime_TR2 = self.blocks('B20').SPRemote().value
        deadtime_air2= self.blocks('B33').SPRemote().value
        return deadtime_TR1, deadtime_TR2, deadtime_air2

    def run_step(self, steps, episodes):
        ep_step_time = self.max_ep_step * self.dt
        self.sim.endtime = self.dt + ep_step_time * episodes + self.dt * steps
        # 下一步模擬暫停的時間 = 每步模擬時間+ 初始到上一個訓練集的模擬總時間 + 本次訓練集的模擬時間

        self.sim.run(1)
        # 進行模擬

