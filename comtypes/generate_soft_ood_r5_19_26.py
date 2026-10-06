"""Generate eight directional Soft-OOD cases around the R5 training rectangle."""

import argparse
import atexit
import csv
import json
from pathlib import Path
import random

import generate_soft_ood_r5_13_14 as base


OUTPUT_DIR = base.OUTPUT_DIR
STAGE_STEPS = base.CONTROL_UPDATE_INTERVAL_MIN
FORMAL_STEPS = 3 * STAGE_STEPS

# Coordinates are (air2 set point, heater-2 temperature set point).
CASE_CONFIGS = {
    "R5-19": {
        "direction": "left",
        "bounds": ((115.0, 135.0), (145.0, 235.0)),
        "warmup": ((125.0, 190.0),),
        "formal": ((125.0, 155.0), (125.0, 190.0), (125.0, 225.0)),
        "jitter": (3.0, 3.0),
    },
    "R5-20": {
        "direction": "right",
        "bounds": ((305.0, 335.0), (145.0, 235.0)),
        "warmup": ((320.0, 190.0),),
        "formal": ((320.0, 155.0), (320.0, 190.0), (320.0, 225.0)),
        "jitter": (4.0, 3.0),
    },
    "R5-21": {
        "direction": "down",
        "bounds": ((145.0, 295.0), (105.0, 135.0)),
        "warmup": ((220.0, 120.0),),
        "formal": ((160.0, 120.0), (220.0, 120.0), (280.0, 120.0)),
        "jitter": (4.0, 3.0),
    },
    "R5-22": {
        "direction": "up",
        "bounds": ((145.0, 295.0), (245.0, 275.0)),
        "warmup": ((220.0, 260.0),),
        "formal": ((160.0, 260.0), (220.0, 260.0), (280.0, 260.0)),
        "jitter": (4.0, 3.0),
    },
    "R5-23": {
        "direction": "upper_left",
        "bounds": ((115.0, 135.0), (245.0, 275.0)),
        "warmup": ((125.0, 190.0), (125.0, 260.0)),
        "formal": ((130.0, 250.0), (120.0, 270.0), (125.0, 260.0)),
        "jitter": (2.0, 2.0),
    },
    "R5-24": {
        "direction": "upper_right",
        "bounds": ((305.0, 335.0), (245.0, 275.0)),
        "warmup": ((320.0, 190.0), (320.0, 260.0)),
        "formal": ((310.0, 250.0), (330.0, 270.0), (320.0, 260.0)),
        "jitter": (2.0, 2.0),
    },
    "R5-25": {
        "direction": "lower_left",
        "bounds": ((115.0, 135.0), (105.0, 135.0)),
        "warmup": ((125.0, 190.0), (125.0, 120.0)),
        "formal": ((130.0, 110.0), (120.0, 130.0), (125.0, 120.0)),
        "jitter": (2.0, 2.0),
    },
    "R5-26": {
        "direction": "lower_right",
        "bounds": ((305.0, 335.0), (105.0, 135.0)),
        "warmup": ((320.0, 190.0), (320.0, 120.0)),
        "formal": ((310.0, 110.0), (330.0, 130.0), (320.0, 120.0)),
        "jitter": (2.0, 2.0),
    },
}

CATEGORY_BY_DIRECTION = {
    "left": "air2_only_soft_ood",
    "right": "air2_only_soft_ood",
    "down": "t2_only_soft_ood",
    "up": "t2_only_soft_ood",
    "upper_left": "both_ood",
    "upper_right": "both_ood",
    "lower_left": "both_ood",
    "lower_right": "both_ood",
}


def in_region(row, bounds, measured_air2=False):
    x_column = "second_air2" if measured_air2 else "air2_SP"
    x = float(row[x_column])
    y = float(row["HEATER2_output_T_SP"])
    return bounds[0][0] <= x <= bounds[0][1] and bounds[1][0] <= y <= bounds[1][1]


class CompassInputs:
    def __init__(self, config, seed):
        self.rng = random.Random(seed)
        self.warmup_stages = len(config["warmup"])
        x_jitter, y_jitter = config["jitter"]
        self.targets = list(config["warmup"]) + [
            (
                x + self.rng.uniform(-x_jitter, x_jitter),
                y + self.rng.uniform(-y_jitter, y_jitter),
            )
            for x, y in config["formal"]
        ]
        self.current_inlet = None

    def capture_initial_controls(self, env):
        self.initial_x = float(env.blocks("B33").SP.value)
        self.initial_y = float(env.blocks("B20").SP.value)

    def inlet_values(self, global_step):
        if global_step % base.INLET_UPDATE_INTERVAL_MIN == 0:
            total_flow = base.bounded_gauss(self.rng, 140.0, 4.0, 125.0, 155.0)
            inlet_t = base.bounded_gauss(self.rng, 83.6, 0.22, 82.8, 84.4)
            inlet_p = base.bounded_gauss(self.rng, 1.675, 0.003, 1.665, 1.685)
            self.current_inlet = (
                total_flow * 0.2857,
                total_flow * 0.3232,
                total_flow * 0.3911,
                inlet_t,
                inlet_p,
            )
        return self.current_inlet

    def control_values(self, env, global_step):
        stage = global_step // STAGE_STEPS
        stage_step = global_step % STAGE_STEPS
        target_x, target_y = self.targets[stage]
        previous_x, previous_y = (
            (self.initial_x, self.initial_y) if stage == 0 else self.targets[stage - 1]
        )
        if stage_step < base.CONTROL_DEAD_TIME_MIN:
            x, y = previous_x, previous_y
        elif stage_step < base.CONTROL_DEAD_TIME_MIN + base.CONTROL_RAMP_TIME_MIN:
            ramp_fraction = (
                (stage_step - base.CONTROL_DEAD_TIME_MIN)
                / (base.CONTROL_RAMP_TIME_MIN - 1)
            )
            x = previous_x + ramp_fraction * (target_x - previous_x)
            y = previous_y + ramp_fraction * (target_y - previous_y)
        else:
            x, y = target_x, target_y
        tr1 = env.blocks("B21").SP.value
        return tr1, y, x


def assert_schedule(case_name, inputs):
    config = CASE_CONFIGS[case_name]
    bounds = config["bounds"]
    for target in inputs.targets[inputs.warmup_stages - 1:]:
        if not (bounds[0][0] < target[0] < bounds[0][1]):
            raise ValueError(f"{case_name} target air2 is outside its region: {target}")
        if not (bounds[1][0] < target[1] < bounds[1][1]):
            raise ValueError(f"{case_name} target T2 is outside its region: {target}")


def build_report(case_name, rows, inputs, seed, warmup_steps, failures):
    config = CASE_CONFIGS[case_name]
    report = base.build_report(case_name, rows, warmup_steps, failures, seed)
    report.update(
        {
            "direction": config["direction"],
            "planned_region": {
                "air2": config["bounds"][0],
                "t2": config["bounds"][1],
            },
            "warmup_targets": inputs.targets[:inputs.warmup_stages],
            "formal_targets": inputs.targets[inputs.warmup_stages:],
            "directional_region_rows": sum(
                in_region(row, config["bounds"]) for row in rows
            ),
            "measured_air2_region_rows": sum(
                in_region(row, config["bounds"], measured_air2=True) for row in rows
            ),
            "actual_second_air2_min_max": {
                "min": min(float(row["second_air2"]) for row in rows),
                "max": max(float(row["second_air2"]) for row in rows),
            },
        }
    )
    return report


def assert_acceptance(case_name, rows, inputs, report):
    expected = CATEGORY_BY_DIRECTION[CASE_CONFIGS[case_name]["direction"]]
    if report["formal_rows"] != FORMAL_STEPS:
        raise RuntimeError(f"{case_name}: expected {FORMAL_STEPS} formal rows")
    if report[expected]["rows"] != FORMAL_STEPS:
        raise RuntimeError(f"{case_name}: wrong Soft-OOD category")
    if report["outside_gain_ann_envelope"]["rows"] != 0:
        raise RuntimeError(f"{case_name}: a Gain ANN input left its envelope")
    if report["directional_region_rows"] != FORMAL_STEPS:
        raise RuntimeError(f"{case_name}: set points left the planned region")
    if report["measured_air2_region_rows"] != FORMAL_STEPS:
        raise RuntimeError(f"{case_name}: measured second-air flow left the planned region")
    if report["aspen_failures_or_nonconvergence"] != 0:
        raise RuntimeError(f"{case_name}: Aspen failures were recorded")
    for stage, target in enumerate(inputs.targets[inputs.warmup_stages:]):
        row = rows[(stage + 1) * STAGE_STEPS - 1]
        actual = (float(row["air2_SP"]), float(row["HEATER2_output_T_SP"]))
        if any(abs(value - planned) > 0.01 for value, planned in zip(actual, target)):
            raise RuntimeError(f"{case_name}: formal stage {stage + 1} missed {target}")


def run_case(args, case_name):
    config = CASE_CONFIGS[case_name]
    output_path = OUTPUT_DIR / f"Test_dataform_change_air2_R=5-{case_name[3:]}.csv"
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {output_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    seed = random.SystemRandom().getrandbits(64)
    inputs = CompassInputs(config, seed)
    assert_schedule(case_name, inputs)
    warmup_steps = inputs.warmup_stages * STAGE_STEPS
    total_steps = warmup_steps + FORMAL_STEPS
    warmup_path = output_path.with_name(f"{output_path.stem}_warmup_seed-{seed}.csv")
    partial_path = output_path.with_name(f"{output_path.stem}_seed-{seed}.partial.csv")
    failure_path = output_path.with_name(f"{output_path.stem}_seed-{seed}.failure.json")
    report_path = OUTPUT_DIR / f"soft_ood_validation_report_{case_name}.json"
    print(f"{case_name} seed={seed}; targets={inputs.targets}", flush=True)

    env = None
    last_attempt = None
    counters = {"aspen_failures_or_nonconvergence": 0}
    recent_warmup = []
    formal_rows = []
    try:
        env = base.Env(
            base.SAMPLE_INTERVAL_MIN,
            total_steps,
            args.aspen_file,
            sync_steps=args.sync_steps,
            record_history=not args.no_record_history,
            batch_com_mode=args.batch_com,
        )
        atexit.register(env.close)
        base.wait_for_aspen_ready(env)
        inputs.capture_initial_controls(env)

        with warmup_path.open("w", encoding="utf-8", newline="") as warmup_file:
            writer = csv.writer(warmup_file)
            base.write_header(writer)
            for global_step in range(warmup_steps):
                inlet = inputs.inlet_values(global_step)
                controls = inputs.control_values(env, global_step)
                last_attempt = {"phase": "warmup", "step": global_step, "inlet": inlet, "controls": controls}
                env.do_dis3(*inlet, *controls)
                base.run_aspen_minute(env, global_step, counters)
                row = base.row_from_aspen(env, global_step)
                base.write_row(writer, global_step, row)
                warmup_file.flush()
                recent_warmup.append(row)
                recent_warmup = recent_warmup[-base.WARMUP_CONFIRMATION_ROWS:]
                if (global_step + 1) % 10 == 0:
                    print(f"{case_name} warmup {global_step + 1}/{warmup_steps}", flush=True)

        if len(recent_warmup) < base.WARMUP_CONFIRMATION_ROWS or any(
            not in_region(row, config["bounds"])
            or not in_region(row, config["bounds"], measured_air2=True)
            or base.classify_row(row)[1]
            for row in recent_warmup
        ):
            raise RuntimeError(f"{case_name}: last 30 warmup rows did not reach the planned region")

        with partial_path.open("w", encoding="utf-8", newline="") as formal_file:
            writer = csv.writer(formal_file)
            base.write_header(writer)
            for formal_index in range(FORMAL_STEPS):
                global_step = warmup_steps + formal_index
                inlet = inputs.inlet_values(global_step)
                controls = inputs.control_values(env, global_step)
                last_attempt = {"phase": "formal", "step": global_step, "inlet": inlet, "controls": controls}
                env.do_dis3(*inlet, *controls)
                base.run_aspen_minute(env, global_step, counters)
                row = base.row_from_aspen(env, formal_index)
                base.write_row(writer, formal_index, row)
                formal_file.flush()
                formal_rows.append(row)
                if (formal_index + 1) % 10 == 0:
                    print(f"{case_name} formal {formal_index + 1}/{FORMAL_STEPS}", flush=True)

        report = build_report(
            case_name, formal_rows, inputs, seed, warmup_steps,
            counters["aspen_failures_or_nonconvergence"],
        )
        assert_acceptance(case_name, formal_rows, inputs, report)
        partial_path.replace(output_path)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"{case_name} accepted: {output_path}; report={report_path}", flush=True)
        return report
    except Exception as exc:
        try:
            status = base.aspen_status(env) if env is not None else None
        except Exception as status_exc:
            status = {"status_read_error": repr(status_exc)}
        failure_path.write_text(
            json.dumps(
                {
                    "case": case_name,
                    "seed": seed,
                    "error": repr(exc),
                    "last_attempt": last_attempt,
                    "aspen_status": status,
                    "warmup_path": str(warmup_path),
                    "partial_path": str(partial_path),
                    "targets": inputs.targets,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        raise
    finally:
        if env is not None:
            atexit.unregister(env.close)
            try:
                env.close()
            except Exception as close_exc:
                print(f"Warning: Aspen close failed: {close_exc!r}", flush=True)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=(*CASE_CONFIGS, "all"), default="R5-19")
    parser.add_argument("--aspen-file", default=base.DEFAULT_ASPEN_FILE)
    parser.add_argument("--sync-steps", choices=("Full", "Low", "Medium", "High"), default="Full")
    parser.add_argument("--no-record-history", action="store_true")
    parser.add_argument("--batch-com", choices=("off", "validate", "on"), default="off")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    case_names = tuple(CASE_CONFIGS) if args.case == "all" else (args.case,)
    if args.dry_run:
        for case_name in case_names:
            inputs = CompassInputs(CASE_CONFIGS[case_name], seed=12345)
            assert_schedule(case_name, inputs)
            print(json.dumps({"case": case_name, "targets": inputs.targets}))
        return

    reports = [run_case(args, case_name) for case_name in case_names]
    if args.case == "all":
        path = OUTPUT_DIR / "soft_ood_validation_report_R5-19_to_R5-26.json"
        path.write_text(json.dumps(reports, indent=2), encoding="utf-8")
        print(f"Aggregate report written to {path}")


if __name__ == "__main__":
    main()
