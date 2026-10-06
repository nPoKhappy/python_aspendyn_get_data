import argparse
import atexit
import csv
import json
import math
import os
from pathlib import Path
import random
import time

import numpy as np

from claus_plant_flow_record_custom import Env


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "csv" / "範圍外數據"
DEFAULT_ASPEN_FILE = "claus OK1heaterdis1H2Sincrease try9-2_NEW.dynf"
SAMPLE_INTERVAL_MIN = 1
INLET_UPDATE_INTERVAL_MIN = 10
CONTROL_UPDATE_INTERVAL_MIN = 480
CONTROL_DEAD_TIME_MIN = 10
CONTROL_RAMP_TIME_MIN = 300
DEFAULT_WARMUP_STEPS = 480
DEFAULT_FORMAL_STEPS = 1440
WARMUP_CONFIRMATION_ROWS = 30
ASPEN_READY_TIMEOUT_SECONDS = 120

INDEX_COLUMNS = [
    "i", "j", "steps", "acidgas_Fm", "acidgas_Fv", "acidgas_CO2",
    "acidgas_H2O", "acidgas_H2S", "acidgas_T", "acidgas_P", "air",
    "air_SP", "second_air2", "air2_SP", "COG", "COG_SP",
    "burner_input_T_SP", "burner_input_T_PV", "burner_inputP",
    "burner_output_T_SP", "burner_output_T_PV", "burner_output_P_SP",
    "burner_output_P_PV", "fur_F", "fur_inputT", "fur_inputP",
    "fur_temp", "fur_outputT", "fur_outputP_SP", "fur_outputP_PV",
    "WHB_F", "WHB_inputT", "WHB_inputP", "WHB_outputT", "WHB_outputP",
    "SEP1_F", "SEP1_P_SP", "SEP1_P_PV", "SEP1_T", "HEATER1_F",
    "HEATER1_input_T", "HEATER1_input_P", "HEATER1_output_T_SP",
    "HEATER1_output_T_PV", "HEATER1_output_P", "cat1_F",
    "cat1_input_temp", "cat1_output_temp", "cat1_input_P",
    "cat1_output_P_SP", "cat1_output_P_PV", "cat1_deltaP", "SEP2_F",
    "SEP2_P_SP", "SEP2_P_PV", "SEP2_T", "HEATER2_F",
    "HEATER2_input_T", "HEATER2_input_P", "HEATER2_output_T_SP",
    "HEATER2_output_T_PV", "HEATER2_output_P", "cat2_F",
    "cat2_input_temp", "cat2_output_temp", "cat2_input_P",
    "cat2_output_P_SP", "cat2_output_P_PV", "cat2_deltaP", "SEP3_F",
    "SEP3_P_SP", "SEP3_P_PV", "SEP3_T", "B35_H2S", "B35_SO2",
    "ratio", "ratioSP", "conv",
]

ANN_RANGES = {
    "air2_SP": (110.0, 340.0),
    "HEATER2_output_T_SP": (100.0, 280.0),
    "acidgas_Fm": (110.5, 160.5),
    "acidgas_T": (82.6, 84.6),
    "acidgas_P": (1.66, 1.69),
}
TRANSFORMER_RANGES = {
    "air2_SP": (140.0, 300.0),
    "HEATER2_output_T_SP": (140.0, 240.0),
}
CASE_CONFIGS = {
    "R5-15": {
        "air2_range": (305.0, 335.0),
        "t2_range": (180.0, 200.0),
        "expected_category": "air2_only_soft_ood",
        "output_name": "Test_dataform_change_air2_R=5-15.csv",
    },
    "R5-16": {
        "air2_range": (180.0, 220.0),
        "t2_range": (243.0, 277.0),
        "expected_category": "t2_only_soft_ood",
        "output_name": "Test_dataform_change_air2_R=5-16.csv",
    },
    "R5-17": {
        "air2_range": (305.0, 335.0),
        "t2_range": (180.0, 200.0),
        "expected_category": "air2_only_soft_ood",
        "output_name": "Test_dataform_change_air2_R=5-17.csv",
    },
    "R5-18": {
        "air2_range": (180.0, 220.0),
        "t2_range": (243.0, 277.0),
        "expected_category": "t2_only_soft_ood",
        "output_name": "Test_dataform_change_air2_R=5-18.csv",
    },
}


def bounded_gauss(rng, mean, stddev, lower, upper):
    """Draw from a Gaussian without clipping the sampled value."""
    while True:
        value = rng.gauss(mean, stddev)
        if lower <= value <= upper:
            return value


def in_closed_range(value, limits):
    return limits[0] <= value <= limits[1]


def classify_row(row):
    gain_violation = any(
        not in_closed_range(float(row[name]), limits)
        for name, limits in ANN_RANGES.items()
    )
    air_in = in_closed_range(
        float(row["air2_SP"]), TRANSFORMER_RANGES["air2_SP"]
    )
    t2_in = in_closed_range(
        float(row["HEATER2_output_T_SP"]),
        TRANSFORMER_RANGES["HEATER2_output_T_SP"],
    )
    if air_in and t2_in:
        category = "transformer_in_range"
    elif not air_in and t2_in:
        category = "air2_only_soft_ood"
    elif air_in and not t2_in:
        category = "t2_only_soft_ood"
    else:
        category = "both_ood"
    return category, gain_violation


class SoftOodInputs:
    def __init__(self, case_name, total_steps, seed):
        self.config = CASE_CONFIGS[case_name]
        self.rng = random.Random(seed)
        stage_count = math.ceil(total_steps / CONTROL_UPDATE_INTERVAL_MIN)
        air_lower, air_upper = self.config["air2_range"]
        t2_lower, t2_upper = self.config["t2_range"]
        self.air2_targets = [(air_lower + air_upper) / 2]
        self.t2_targets = [(t2_lower + t2_upper) / 2]
        for _ in range(1, stage_count):
            self.air2_targets.append(
                bounded_gauss(
                    self.rng,
                    (air_lower + air_upper) / 2,
                    (air_upper - air_lower) / 6,
                    air_lower,
                    air_upper,
                )
            )
            self.t2_targets.append(
                bounded_gauss(
                    self.rng,
                    (t2_lower + t2_upper) / 2,
                    (t2_upper - t2_lower) / 6,
                    t2_lower,
                    t2_upper,
                )
            )
        self.current_inlet = None

    def inlet_values(self, global_step):
        if global_step % INLET_UPDATE_INTERVAL_MIN == 0:
            total_flow = bounded_gauss(self.rng, 140.0, 4.0, 125.0, 155.0)
            inlet_t = bounded_gauss(self.rng, 83.6, 0.22, 82.8, 84.4)
            inlet_p = bounded_gauss(self.rng, 1.675, 0.003, 1.665, 1.685)
            self.current_inlet = (
                total_flow * 0.2857,
                total_flow * 0.3232,
                total_flow * 0.3911,
                inlet_t,
                inlet_p,
            )
        return self.current_inlet

    def control_values(self, env, global_step):
        stage = global_step // CONTROL_UPDATE_INTERVAL_MIN
        stage_step = global_step % CONTROL_UPDATE_INTERVAL_MIN
        tr1 = env.blocks("B21").SP.value
        target_t2 = self.t2_targets[stage]
        target_air2 = self.air2_targets[stage]

        if stage == 0:
            previous_t2 = self.initial_t2
            previous_air2 = self.initial_air2
        else:
            previous_t2 = self.t2_targets[stage - 1]
            previous_air2 = self.air2_targets[stage - 1]

        if stage_step < CONTROL_DEAD_TIME_MIN:
            t2 = previous_t2
            air2 = previous_air2
        elif stage_step < CONTROL_DEAD_TIME_MIN + CONTROL_RAMP_TIME_MIN:
            ramp_index = stage_step - CONTROL_DEAD_TIME_MIN
            t2 = np.linspace(
                previous_t2, target_t2, CONTROL_RAMP_TIME_MIN
            )[ramp_index]
            air2 = np.linspace(
                previous_air2, target_air2, CONTROL_RAMP_TIME_MIN
            )[ramp_index]
        else:
            t2 = target_t2
            air2 = target_air2
        return tr1, float(t2), float(air2)

    def capture_initial_controls(self, env):
        self.initial_t2 = float(env.blocks("B20").SP.value)
        self.initial_air2 = float(env.blocks("B33").SP.value)


def row_from_aspen(env, formal_index):
    values = np.asarray(env.data_conclusion(), dtype=float)
    if values.shape != (75,):
        raise RuntimeError(f"Expected 75 Aspen values, received shape {values.shape}")
    full_values = np.concatenate(([0.0, float(formal_index), float(formal_index)], values))
    return dict(zip(INDEX_COLUMNS, full_values, strict=True))


def aspen_status(env):
    return {
        "state": str(env.sim.State),
        "spec_state": str(env.sim.SpecState),
        "degrees": int(env.sim.Degrees),
        "run_mode": str(env.sim.RunMode),
        "time": float(env.sim.Time),
        "document": str(env.adyn.ActiveDocument.FullName),
    }


def wait_for_aspen_ready(env):
    deadline = time.monotonic() + ASPEN_READY_TIMEOUT_SECONDS
    last_status = None
    while time.monotonic() < deadline:
        last_status = aspen_status(env)
        ready_state = last_status["state"] in {"Ready", "Paused"}
        if (
            ready_state
            and last_status["spec_state"] == "Complete"
            and last_status["degrees"] == 0
        ):
            env.sim.RunMode = "Dynamic"
            env.sim.Termination = "AtTime"
            print(f"Aspen ready: {last_status}")
            return
        print(f"Waiting for Aspen readiness: {last_status}")
        time.sleep(1)
    raise TimeoutError(f"Aspen was not ready after 120 seconds: {last_status}")


def run_aspen_minute(env, global_step, counters):
    env.sim.endtime = (global_step + 1) * SAMPLE_INTERVAL_MIN
    try:
        env.sim.run(1)
        if not bool(env.sim.Successful):
            counters["aspen_failures_or_nonconvergence"] += 1
            raise RuntimeError(f"Aspen did not converge at global step {global_step}")
    except Exception as exc:
        if counters["aspen_failures_or_nonconvergence"] == 0:
            counters["aspen_failures_or_nonconvergence"] += 1
        try:
            status = aspen_status(env)
        except Exception as status_exc:
            status = {"status_read_error": repr(status_exc)}
        raise RuntimeError(
            f"Aspen run failed at global step {global_step}; status={status}"
        ) from exc


def write_header(writer):
    # Preserve the unnamed pandas index column used by R5-11 and R5-12.
    writer.writerow([""] + INDEX_COLUMNS)


def write_row(writer, csv_index, row):
    writer.writerow([csv_index] + [row[name] for name in INDEX_COLUMNS])


def build_report(case_name, rows, warmup_rows, failure_count, seed):
    total = len(rows)
    categories = {
        "transformer_in_range": 0,
        "air2_only_soft_ood": 0,
        "t2_only_soft_ood": 0,
        "both_ood": 0,
    }
    gain_violations = 0
    for row in rows:
        category, gain_violation = classify_row(row)
        categories[category] += 1
        gain_violations += int(gain_violation)

    def count_and_ratio(count):
        return {"rows": count, "ratio": count / total if total else 0.0}

    report = {
        "case": case_name,
        "seed": seed,
        "formal_rows": total,
        "actual_ann_input_min_max": {
            name: {
                "min": min(float(row[name]) for row in rows),
                "max": max(float(row[name]) for row in rows),
            }
            for name in ANN_RANGES
        },
        "transformer_in_range": count_and_ratio(categories["transformer_in_range"]),
        "air2_only_soft_ood": count_and_ratio(categories["air2_only_soft_ood"]),
        "t2_only_soft_ood": count_and_ratio(categories["t2_only_soft_ood"]),
        "both_ood": count_and_ratio(categories["both_ood"]),
        "outside_gain_ann_envelope": count_and_ratio(gain_violations),
        "warmup_rows": warmup_rows,
        "aspen_failures_or_nonconvergence": failure_count,
    }
    return report


def assert_acceptance(case_name, report):
    expected = CASE_CONFIGS[case_name]["expected_category"]
    total = report["formal_rows"]
    failures = []
    if report[expected]["rows"] != total:
        failures.append(f"{expected} is not 100%")
    for category in (
        "transformer_in_range",
        "both_ood",
        "outside_gain_ann_envelope",
    ):
        if report[category]["rows"] != 0:
            failures.append(f"{category} is not 0%")
    other_single_ood = (
        "t2_only_soft_ood" if expected == "air2_only_soft_ood"
        else "air2_only_soft_ood"
    )
    if report[other_single_ood]["rows"] != 0:
        failures.append(f"{other_single_ood} is not 0%")
    if failures:
        raise RuntimeError(f"{case_name} acceptance failed: " + "; ".join(failures))


def run_case(args, case_name):
    config = CASE_CONFIGS[case_name]
    output_path = OUTPUT_DIR / config["output_name"]
    if output_path.exists() and not args.overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {output_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total_steps = args.warmup_steps + args.formal_steps
    seed = random.SystemRandom().getrandbits(64)
    inputs = SoftOodInputs(case_name, total_steps, seed)
    partial_path = output_path.with_name(f"{output_path.stem}_seed-{seed}.partial.csv")
    warmup_path = output_path.with_name(f"{output_path.stem}_warmup_seed-{seed}.csv")
    print(f"{case_name} random seed={seed}; warmup={warmup_path}")
    counters = {"aspen_failures_or_nonconvergence": 0}
    formal_rows = []
    recent_warmup_rows = []
    env = Env(
        SAMPLE_INTERVAL_MIN,
        total_steps,
        args.aspen_file,
        sync_steps=args.sync_steps,
        record_history=not args.no_record_history,
        batch_com_mode=args.batch_com,
    )
    atexit.register(env.close)
    wait_for_aspen_ready(env)
    inputs.capture_initial_controls(env)

    try:
        with warmup_path.open("w", encoding="utf-8", newline="") as warmup_file:
            warmup_writer = csv.writer(warmup_file)
            write_header(warmup_writer)
            for global_step in range(args.warmup_steps):
                inlet_values = inputs.inlet_values(global_step)
                control_values = inputs.control_values(env, global_step)
                env.do_dis3(*inlet_values, *control_values)
                run_aspen_minute(env, global_step, counters)
                row = row_from_aspen(env, global_step)
                write_row(warmup_writer, global_step, row)
                recent_warmup_rows.append(row)
                recent_warmup_rows = recent_warmup_rows[-WARMUP_CONFIRMATION_ROWS:]
                print(f"{case_name} warmup {global_step + 1}/{args.warmup_steps}")

        expected = config["expected_category"]
        if len(recent_warmup_rows) < WARMUP_CONFIRMATION_ROWS or any(
            classify_row(row) != (expected, False) for row in recent_warmup_rows
        ):
            raise RuntimeError(
                f"{case_name} warmup did not finish with "
                f"{WARMUP_CONFIRMATION_ROWS} consecutive valid {expected} rows"
            )

        with partial_path.open("w", encoding="utf-8", newline="") as formal_file:
            formal_writer = csv.writer(formal_file)
            write_header(formal_writer)
            for formal_index in range(args.formal_steps):
                global_step = args.warmup_steps + formal_index
                inlet_values = inputs.inlet_values(global_step)
                control_values = inputs.control_values(env, global_step)
                env.do_dis3(*inlet_values, *control_values)
                run_aspen_minute(env, global_step, counters)
                row = row_from_aspen(env, formal_index)
                formal_rows.append(row)
                write_row(formal_writer, formal_index, row)
                formal_file.flush()
                print(f"{case_name} formal {formal_index + 1}/{args.formal_steps}")

        report = build_report(
            case_name,
            formal_rows,
            args.warmup_steps,
            counters["aspen_failures_or_nonconvergence"],
            seed,
        )
        assert_acceptance(case_name, report)
        if output_path.exists():
            output_path.unlink()
        partial_path.replace(output_path)
        return report
    finally:
        atexit.unregister(env.close)
        try:
            env.close()
        except Exception as close_exc:
            print(f"Warning: Aspen close failed: {close_exc!r}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate and validate R5-15 through R5-18 Soft-OOD Aspen Dynamics data."
    )
    parser.add_argument(
        "--case", choices=(*CASE_CONFIGS, "both", "all"), default="all"
    )
    parser.add_argument("--warmup-steps", type=int, default=DEFAULT_WARMUP_STEPS)
    parser.add_argument("--formal-steps", type=int, default=DEFAULT_FORMAL_STEPS)
    parser.add_argument("--aspen-file", default=DEFAULT_ASPEN_FILE)
    parser.add_argument(
        "--sync-steps", choices=("Full", "Low", "Medium", "High"), default="Full"
    )
    parser.add_argument("--no-record-history", action="store_true")
    parser.add_argument(
        "--batch-com", choices=("off", "validate", "on"), default="off"
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.warmup_steps < WARMUP_CONFIRMATION_ROWS:
        parser.error(
            f"--warmup-steps must be at least {WARMUP_CONFIRMATION_ROWS}"
        )
    if args.formal_steps <= 0:
        parser.error("--formal-steps must be greater than zero")
    return args


def main():
    args = parse_args()
    if args.case == "all":
        case_names = tuple(CASE_CONFIGS)
    elif args.case == "both":
        case_names = ("R5-15", "R5-16")
    else:
        case_names = (args.case,)
    reports = []
    for case_name in case_names:
        reports.append(run_case(args, case_name))
        print(json.dumps(reports[-1], ensure_ascii=False, indent=2))

    report_suffix = "_".join(case_names)
    report_path = OUTPUT_DIR / f"soft_ood_validation_report_{report_suffix}.json"
    report_path.write_text(
        json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Validation report written to {report_path}")


if __name__ == "__main__":
    main()
