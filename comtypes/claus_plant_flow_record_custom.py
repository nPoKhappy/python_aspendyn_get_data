import gc
import random
import subprocess

import comtypes

import numpy as np

from claus_plant_flow_record import Env as ComtypesEnv


DEFAULT_ASPEN_FILE_NAME = "claus OK1heaterdis1H2Sincrease try9-2.dynf"


def tr2_mean_for_completed_files(completed_file_count):
    return 300 + 20 * (completed_file_count // 2)


class Env(ComtypesEnv):
    """comtypes implementation of the custom Claus plant data recorder."""

    def __init__(
        self,
        dt,
        MAX_EP_STEPS,
        aspen_file_name=DEFAULT_ASPEN_FILE_NAME,
        tr2_mean=200,
        sync_steps="Full",
        record_history=True,
        batch_com_mode="off",
    ):
        if sync_steps not in {"Full", "Low", "Medium", "High"}:
            raise ValueError(
                "sync_steps must be Full, Low, Medium, or High"
            )
        if batch_com_mode not in {"off", "validate", "on"}:
            raise ValueError(
                "batch_com_mode must be off, validate, or on"
            )

        # Reuse the Aspen launch, COM connection, and compatibility wrapper from
        # the standard comtypes implementation.
        self.tr2_mean = tr2_mean
        self.batch_com_mode = batch_com_mode
        self._batch_data_paths = ()
        self._batch_data_slot_indices = ()
        self._batch_write_paths = ()
        self._batch_write_variables = ()

        try:
            super().__init__(dt, MAX_EP_STEPS, aspen_file_name)
            self.sim.options.SyncSteps = sync_steps
            self.sim.options.TimeSettings.RecordHistory = bool(record_history)
            if batch_com_mode != "off":
                self._initialize_batch_com()
        except Exception:
            try:
                self.close()
            except Exception:
                pass
            raise

        print(
            "Aspen execution settings: "
            f"SyncSteps={sync_steps}, "
            f"RecordHistory={bool(record_history)}, "
            f"BatchCOM={batch_com_mode}"
        )
        if batch_com_mode == "validate":
            print(
                "Batch COM validation mode runs both legacy and batch reads; "
                "use it only for a short correctness test."
            )

    def close(self):
        adyn = getattr(self, "adyn", None)
        if adyn is None:
            return

        quit_error = None
        try:
            adyn.Quit()
        except (OSError, comtypes.COMError) as exc:
            quit_error = exc
        finally:
            self._batch_data_paths = ()
            self._batch_data_slot_indices = ()
            self._batch_write_paths = ()
            self._batch_write_variables = ()
            self.blocks = None
            self.streams = None
            self.fsheet = None
            self.sim = None
            self.adyn = None
            adyn = None
            gc.collect()

        process = getattr(self, "ad_process", None)
        if process is not None:
            try:
                process.wait(timeout=60)
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError(
                    "Aspen Dynamics did not exit within 60 seconds"
                ) from exc
            finally:
                self.ad_process = None

        if quit_error is not None:
            raise RuntimeError("Aspen Dynamics Quit() failed") from quit_error

    def _initialize_batch_com(self):
        data_variables = (
            # Input: raw values 0-8.
            self.streams("ACIDGAS").F,
            self.streams("ACIDGAS").Fv,
            self.streams("ACIDGAS").Fcn("CO2"),
            self.streams("ACIDGAS").Fcn("H2O"),
            self.streams("ACIDGAS").Fcn("H2S"),
            self.streams("ACIDGAS").T,
            self.streams("ACIDGAS").P,
            self.streams("AIR").F,
            self.blocks("B17").SP,
            # Burner: raw values 9-19.
            self.streams("AIR2").Fv,
            self.blocks("B33").SP,
            self.streams("S4").Fv,
            self.blocks("B35").SP,
            self.blocks("B18").SP,
            self.blocks("B18").PV,
            self.streams("S8").P,
            self.blocks("B19").SP,
            self.blocks("B19").PV,
            self.blocks("BURNER_PC").SP,
            self.blocks("BURNER_PC").PV,
            # Furnace: raw values 20-26.
            self.streams("S12").F,
            self.blocks("FURANCE").T(0),
            self.streams("S12").P,
            self.blocks("FURANCE").T(1),
            self.streams("S15").T,
            self.blocks("FURANCE_PC").SP,
            self.blocks("FURANCE_PC").PV,
            # WHB: raw values 27-31.
            self.streams("S16").F,
            self.streams("S16").T,
            self.streams("S16").P,
            self.streams("S13").T,
            self.streams("S13").P,
            # SEP1: raw values 32-35.
            self.streams("S14").F,
            self.blocks("SEP1_PC").SP,
            self.blocks("SEP1_PC").PV,
            self.blocks("SEP1").T,
            # HEATER1: raw values 36-41.
            self.streams("S36").F,
            self.streams("S36").T,
            self.streams("S36").P,
            self.blocks("B21").SP,
            self.blocks("B21").PV,
            self.streams("S20").P,
            # CAT1: raw values 42-47.
            self.streams("S21").F,
            self.streams("S21").T,
            self.streams("S22").T,
            self.streams("S21").P,
            self.blocks("CAT1_PC").SP,
            self.blocks("CAT1_PC").PV,
            # SEP2: raw values 48-51.
            self.streams("S23").F,
            self.blocks("SEP2_PC").SP,
            self.blocks("SEP2_PC").PV,
            self.blocks("SEP2").T,
            # HEATER2: raw values 52-57.
            self.streams("S25").F,
            self.streams("S25").T,
            self.streams("S25").P,
            self.blocks("B20").SP,
            self.blocks("B20").PV,
            self.streams("S20").P,
            # CAT2: raw values 58-63.
            self.streams("S27").F,
            self.streams("S27").T,
            self.streams("S28").T,
            self.streams("S27").P,
            self.blocks("CAT2_PC").SP,
            self.blocks("CAT2_PC").PV,
            # SEP3: raw values 64-67.
            self.streams("S29").F,
            self.blocks("SEP3_PC").SP,
            self.blocks("SEP3_PC").PV,
            self.blocks("SEP3").T,
            # Outlet and conversion inputs: raw values 68-73.
            self.streams("S33").Zn("H2S"),
            self.streams("S33").Zn("SO2"),
            self.streams("S33").Fcn("H2S"),
            self.streams("S33").Fcn("SO2"),
            self.streams("ACIDGAS").Fcn("H2S"),
            self.blocks("B23").SPRemote(),
        )
        write_variables = (
            self.streams("ACIDGAS").FcR("CO2"),
            self.streams("ACIDGAS").FcR("H2O"),
            self.streams("ACIDGAS").FcR("H2S"),
            self.streams("ACIDGAS").T,
            self.streams("ACIDGAS").P,
            self.blocks("B20").SP,
            self.blocks("B33").SP,
        )

        raw_flowsheet = getattr(self.fsheet, "_com_object", None)
        if hasattr(raw_flowsheet, "_FlagAsMethod"):
            raw_flowsheet._FlagAsMethod(
                "GetVariableValues",
                "SetVariableValues",
            )
        for variable in data_variables + write_variables:
            raw_variable = getattr(variable, "_com_object", None)
            if hasattr(raw_variable, "_FlagAsMethod"):
                raw_variable._FlagAsMethod("GetPath")

        data_slot_paths = tuple(
            variable.GetPath() for variable in data_variables
        )
        unique_data_paths = []
        path_to_index = {}
        data_slot_indices = []
        for path in data_slot_paths:
            if path not in path_to_index:
                path_to_index[path] = len(unique_data_paths)
                unique_data_paths.append(path)
            data_slot_indices.append(path_to_index[path])

        self._batch_data_paths = tuple(unique_data_paths)
        self._batch_data_slot_indices = tuple(data_slot_indices)
        self._batch_write_paths = tuple(
            variable.GetPath() for variable in write_variables
        )
        if len(self._batch_data_slot_indices) != 74:
            raise RuntimeError(
                "Batch COM setup expected 74 legacy data positions, got "
                f"{len(self._batch_data_slot_indices)}"
            )
        if len(self._batch_data_paths) != 72:
            raise RuntimeError(
                "Batch COM setup expected 72 unique data paths, got "
                f"{len(self._batch_data_paths)}"
            )
        if len(self._batch_write_paths) != 7:
            raise RuntimeError(
                "Batch COM setup expected 7 write paths, got "
                f"{len(self._batch_write_paths)}"
            )

        if self.batch_com_mode == "validate":
            self._batch_write_variables = write_variables
        print(
            "Batch COM paths prepared: "
            f"{len(self._batch_data_paths)} unique reads mapped to "
            f"{len(self._batch_data_slot_indices)} legacy positions, "
            f"{len(self._batch_write_paths)} writes"
        )

    def get_input_composition(self):
        acidgas_Fm = self.streams("ACIDGAS").F.value
        acidgas_Fv = self.streams("ACIDGAS").Fv.value
        acidgas_CO2 = self.streams("ACIDGAS").Fcn("CO2").value
        acidgas_H2O = self.streams("ACIDGAS").Fcn("H2O").value
        acidgas_H2S = self.streams("ACIDGAS").Fcn("H2S").value
        acidgas_T = self.streams("ACIDGAS").T.value
        acidgas_P = self.streams("ACIDGAS").P.value
        air = self.streams("AIR").F.value
        air_SP = self.blocks("B17").SP.value
        return (
            acidgas_Fm,
            acidgas_Fv,
            acidgas_CO2,
            acidgas_H2O,
            acidgas_H2S,
            acidgas_T,
            acidgas_P,
            air,
            air_SP,
        )

    def _data_conclusion_legacy(self):
        input_data = self.get_input_composition()
        burner_data = self.get_burner_composition()
        furance_data = self.get_furance_composition()
        whb_data = self.get_WHB_composition()
        sep1_data = self.get_SEP1_composition()
        heater1_data = self.get_HEATER1_composition()
        cat1_data = self.get_cat1_composition()
        sep2_data = self.get_SEP2_composition()
        heater2_data = self.get_HEATER2_composition()
        cat2_data = self.get_cat2_composition()
        sep3_data = self.get_SEP3_composition()
        outlet_data = self.get_composition()

        return np.concatenate(
            [
                np.asarray(values)
                for values in (
                    input_data,
                    burner_data,
                    furance_data,
                    whb_data,
                    sep1_data,
                    heater1_data,
                    cat1_data,
                    sep2_data,
                    heater2_data,
                    cat2_data,
                    sep3_data,
                    outlet_data,
                )
            ]
        )

    @staticmethod
    def _rebuild_batch_data(raw_values):
        raw = np.asarray(raw_values, dtype=float)
        if raw.shape != (74,):
            raise RuntimeError(
                "Batch COM read expected 74 values, got "
                f"shape {raw.shape}"
            )

        result = np.asarray(
            [
                *raw[0:48],
                abs(raw[45] - raw[47]) * 1000,
                *raw[48:64],
                abs(raw[61] - raw[63]) * 1000,
                *raw[64:70],
                raw[68] / raw[69],
                raw[73],
                (raw[72] - raw[70] - raw[71]) / raw[72],
            ],
            dtype=float,
        )
        if result.shape != (75,):
            raise RuntimeError(
                "Batch COM reconstruction expected 75 values, got "
                f"shape {result.shape}"
            )
        return result

    def _data_conclusion_batch(self):
        unique_values = tuple(
            self.fsheet.GetVariableValues(self._batch_data_paths)
        )
        if len(unique_values) != len(self._batch_data_paths):
            raise RuntimeError(
                "Batch COM read expected "
                f"{len(self._batch_data_paths)} unique values, got "
                f"{len(unique_values)}"
            )
        raw_values = tuple(
            unique_values[index]
            for index in self._batch_data_slot_indices
        )
        return self._rebuild_batch_data(raw_values)

    @staticmethod
    def _print_data_summary(data):
        print("inlet_F=", np.array([data[0]]))
        print("mole_flowCO2=", np.array([data[2]]))
        print("mole_flowH2O=", np.array([data[3]]))
        print("mole_flowH2S=", np.array([data[4]]))
        print("conv=", np.array([data[74]]))

    def data_conclusion(self):
        if self.batch_com_mode == "off":
            data = self._data_conclusion_legacy()
        elif self.batch_com_mode == "on":
            data = self._data_conclusion_batch()
        else:
            legacy_data = self._data_conclusion_legacy()
            batch_data = self._data_conclusion_batch()
            np.testing.assert_allclose(
                batch_data,
                legacy_data,
                rtol=1e-12,
                atol=1e-12,
                equal_nan=True,
                err_msg="Batch COM read does not match legacy reads",
            )
            print("Batch COM read validation passed for all 75 values.")
            data = legacy_data

        self._print_data_summary(data)
        return data

    def disturbance(self, ram):
        Fn_carbon_dioxide = random.gauss(40.1268, 1.023)
        Fn_hydrogen_dioxide = random.gauss(45.3971, 1.158)
        Fn_hydrogen_sulfide = random.gauss(54.9391, 1.38)
        inlet_T = random.gauss(83.6, 0.4265)
        inlet_P = random.gauss(1.5722 + (0.1 * ram**2), 0.0085)

        print(
            f"F_CO2={Fn_carbon_dioxide:.2f}, "
            f"F_H2O={Fn_hydrogen_dioxide:.2f}, "
            f"F_H2S={Fn_hydrogen_sulfide:.2f}, "
            f"T={inlet_T:.2f}, P={inlet_P:.4f}"
        )
        return (
            Fn_carbon_dioxide,
            Fn_hydrogen_dioxide,
            Fn_hydrogen_sulfide,
            inlet_T,
            inlet_P,
        )

    def do_dis3(self, A, B, C, inlet_T, inlet_P, TR1, TR2, air2):
        # TR1 is observed only in the custom workflow; it is not manipulated.
        write_values = tuple(
            float(value)
            for value in (A, B, C, inlet_T, inlet_P, TR2, air2)
        )
        if self.batch_com_mode == "off":
            self.streams("ACIDGAS").FcR("CO2").Value = A
            self.streams("ACIDGAS").FcR("H2O").Value = B
            self.streams("ACIDGAS").FcR("H2S").Value = C
            self.streams("ACIDGAS").T.value = inlet_T
            self.streams("ACIDGAS").P.value = inlet_P
            self.blocks("B20").SP.value = TR2
            self.blocks("B33").SP.value = air2
        else:
            self.fsheet.SetVariableValues(
                self._batch_write_paths,
                write_values,
            )
            if self.batch_com_mode == "validate":
                read_back = tuple(
                    variable.value
                    for variable in self._batch_write_variables
                )
                np.testing.assert_allclose(
                    read_back,
                    write_values,
                    rtol=1e-12,
                    atol=1e-12,
                    equal_nan=True,
                    err_msg="Batch COM write did not set the requested values",
                )
                print("Batch COM write validation passed for all 7 values.")

        print("inlet_T", inlet_T)
        print("inlet_P", inlet_P)
        return A, B, C, inlet_T, inlet_P, TR1, TR2, air2

    def step_air2_T(self, steps, _episodes):
        self.TR1, self.TR2, self.air2 = self.disturbance_air2_T(steps)
        return self.TR1, self.TR2, self.air2

    def disturbance_air2_T(self, steps):
        dead_time = 10
        ramping_time = 300
        manual_time = 480

        if steps == 0:
            self.op_TR2, self.op_air2 = self.op(manual_time)
            self.deadtime_TR2, self.deadtime_air2 = self.deadtime_SP()

        n = steps % manual_time
        stage = int(steps / manual_time)
        TR1 = self.blocks("B21").SP.value

        if n < dead_time + ramping_time:
            if n < dead_time:
                TR2 = self.blocks("B20").SP.value
                air2 = self.blocks("B33").SP.value
            else:
                if stage == 0:
                    ramp_TR2 = np.linspace(
                        self.deadtime_TR2, self.op_TR2[stage], ramping_time
                    )
                    ramp_air2 = np.linspace(
                        self.deadtime_air2, self.op_air2[stage], ramping_time
                    )
                else:
                    ramp_TR2 = np.linspace(
                        self.op_TR2[stage - 1], self.op_TR2[stage], ramping_time
                    )
                    ramp_air2 = np.linspace(
                        self.op_air2[stage - 1], self.op_air2[stage], ramping_time
                    )
                ramp_index = n - dead_time
                TR2 = ramp_TR2[ramp_index]
                air2 = ramp_air2[ramp_index]
        else:
            TR2 = self.op_TR2[stage]
            air2 = self.op_air2[stage]

        print("TR1=", TR1)
        print("TR2=", TR2)
        print("air2=", air2)
        return TR1, TR2, air2

    def op(self, manual_time):
        operation_count = int(60 * 24 / manual_time)
        op_TR2 = [
            random.gauss(self.tr2_mean, 15) for _ in range(operation_count)
        ]
        op_air2 = [random.gauss(220, 50) for _ in range(operation_count)]
        print("op_TR2=", op_TR2)
        print("op_air2=", op_air2)
        return op_TR2, op_air2

    def deadtime_SP(self):
        deadtime_TR2 = self.blocks("B20").SP.value
        deadtime_air2 = self.blocks("B33").SP.value
        return deadtime_TR2, deadtime_air2
