"""Show planned R5-19–26 regions beside the existing R5-13–18 trajectories."""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comtypes"))
from generate_soft_ood_r5_19_26 import CASE_CONFIGS  # noqa: E402


DATA_DIR = ROOT / "csv" / "範圍外數據"
AIR2 = "second_air2"
T2 = "HEATER2_output_T_SP"


def main():
    fig, ax = plt.subplots(figsize=(8.4, 6.4), constrained_layout=True)
    all_available = all(
        (DATA_DIR / f"Test_dataform_change_air2_R=5-{name[3:]}.csv").is_file()
        for name in CASE_CONFIGS
    )
    ax.add_patch(Rectangle((110, 100), 230, 180, facecolor="#edf3fa", edgecolor="#8ca2bc", label="Gain ANN envelope"))
    ax.add_patch(Rectangle((140, 140), 160, 100, facecolor="white", edgecolor="#202b3c", linewidth=1.5, label="Transformer training range"))

    for number in range(13, 19):
        path = DATA_DIR / f"Test_dataform_change_air2_R=5-{number}.csv"
        if not path.is_file():
            continue
        frame = pd.read_csv(path, usecols=[AIR2, T2])
        ax.plot(frame[AIR2], frame[T2], color="#8a8a8a", linewidth=0.7, alpha=0.45, rasterized=True)

    for name, config in CASE_CONFIGS.items():
        (x0, x1), (y0, y1) = config["bounds"]
        path = DATA_DIR / f"Test_dataform_change_air2_R=5-{name[3:]}.csv"
        available = path.is_file()
        color = "#0072b2" if available else "#d55e00"
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor=color, linewidth=1.3, linestyle="-" if available else "--"))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, name, ha="center", va="center", fontsize=8, color=color,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8, "pad": 0.6})
        if available:
            frame = pd.read_csv(path, usecols=[AIR2, T2])
            ax.plot(frame[AIR2], frame[T2], color=color, linewidth=0.7, alpha=0.6, rasterized=True)

    ax.plot([], [], color="#8a8a8a", label="R5-13–18 actual trajectories")
    ax.plot([], [], color="#0072b2", label="R5-19–26 actual trajectory / region")
    if not all_available:
        ax.plot([], [], color="#d55e00", linestyle="--", label="R5-19–26 planned region only")
    ax.set(xlim=(105, 345), ylim=(95, 285), xlabel="Second-air flow", ylabel="Heater-2 temperature set point")
    ax.grid(alpha=0.18)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=8)
    for suffix in ("png", "pdf"):
        status = "actual" if all_available else "plan"
        output = DATA_DIR / f"mv_coverage_{status}_R5-19_to_R5-26.{suffix}"
        fig.savefig(output, dpi=250)
        print(output)
    plt.close(fig)


if __name__ == "__main__":
    main()
