import argparse
import os
from pathlib import Path
import subprocess
import sys
import time


PROJECT_DIR = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = Path(__file__).with_name("main_claus_flow_record_custom.py")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the custom Claus recorder with an Aspen restart."
    )
    parser.add_argument("--max-ep-steps", type=int)
    parser.add_argument("--max-episodes", type=int)
    parser.add_argument("--run-count", type=int, default=2)
    parser.add_argument(
        "--sync-steps",
        choices=("Full", "Low", "Medium", "High"),
    )
    parser.add_argument(
        "--no-record-history",
        action="store_true",
        help="Do not record all Aspen variable histories during step-by-step runs.",
    )
    parser.add_argument(
        "--batch-com",
        choices=("off", "validate", "on"),
        help=(
            "Use legacy COM calls, compare batch calls with legacy calls, "
            "or use batch calls only."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.max_ep_steps is not None and args.max_ep_steps <= 0:
        raise SystemExit("--max-ep-steps must be greater than zero")
    if args.max_episodes is not None and args.max_episodes <= 0:
        raise SystemExit("--max-episodes must be greater than zero")
    if args.run_count <= 0:
        raise SystemExit("--run-count must be greater than zero")

    child_env = os.environ.copy()
    if args.max_ep_steps is not None:
        child_env["CLAUS_MAX_EP_STEPS"] = str(args.max_ep_steps)
    if args.max_episodes is not None:
        child_env["CLAUS_MAX_EPISODES"] = str(args.max_episodes)
    if args.sync_steps is not None:
        child_env["CLAUS_SYNC_STEPS"] = args.sync_steps
    if args.no_record_history:
        child_env["CLAUS_RECORD_HISTORY"] = "0"
    if args.batch_com is not None:
        child_env["CLAUS_BATCH_COM"] = args.batch_com

    effective_max_ep_steps = int(child_env.get("CLAUS_MAX_EP_STEPS", "1440"))
    effective_max_episodes = int(child_env.get("CLAUS_MAX_EPISODES", "5"))
    child_env["CLAUS_FULL_DATA_FILE_ROWS"] = str(
        effective_max_ep_steps * effective_max_episodes
    )

    all_runs_started = time.perf_counter()
    for run_number in range(1, args.run_count + 1):
        print(f"Starting run {run_number}/{args.run_count}", flush=True)
        run_started = time.perf_counter()
        completed = subprocess.run(
            [sys.executable, str(MAIN_SCRIPT)],
            cwd=PROJECT_DIR,
            env=child_env,
        )
        if completed.returncode != 0:
            raise SystemExit(
                f"Run {run_number}/{args.run_count} failed with exit code "
                f"{completed.returncode}; the next run was not started."
            )
        run_minutes = (time.perf_counter() - run_started) / 60
        print(
            f"Run {run_number}/{args.run_count} completed in "
            f"{run_minutes:.2f} minutes.",
            flush=True,
        )

    total_minutes = (time.perf_counter() - all_runs_started) / 60
    print(
        f"All {args.run_count} runs completed successfully in "
        f"{total_minutes:.2f} minutes."
    )


if __name__ == "__main__":
    main()
