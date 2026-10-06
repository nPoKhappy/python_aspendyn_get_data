"""Create title-free publication figures for the R5 MV trajectories."""

import argparse
import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DEFAULT_DATASETS = {
    "R5": "Test_dataform_change_air2_R=5.csv",
    "R5-1": "Test_dataform_change_air2_R=5-1.csv",
    "R5-2": "Test_dataform_change_air2_R=5-2.csv",
    "R5-6": "Test_dataform_change_air2_R=5-6.csv",
}
OOD_DATASETS = {
    f"R5-{number}": f"Test_dataform_change_air2_R=5-{number}.csv"
    for number in range(13, 19)
}
DATASETS = {**DEFAULT_DATASETS, **OOD_DATASETS}
AIR2_OOD_CASES = {"R5-13", "R5-15", "R5-17"}
OOD_LIMITS = {
    "air2": ((295.0, 340.0), (175.0, 205.0)),
    "t2": ((175.0, 225.0), (235.0, 285.0)),
}
AIR2_COLUMN = "second_air2"
T2_COLUMN = "HEATER2_output_T_SP"
EPISODE_COLUMN = "i"
TRAINING_RANGE = (140.0, 300.0, 140.0, 240.0)

# Okabe-Ito colors: distinguishable under common forms of color blindness.
TRAJECTORY_COLOR = "#0000FF"
START_COLOR = "#009E73"
END_COLOR = "#D55E00"
BOUNDARY_COLOR = "#4D4D4D"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot title-free publication figures for R5 MV trajectories."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("csv/current_training_data"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("csv/current_training_data/publication_plots"),
    )
    parser.add_argument("--no-show", action="store_true")
    parser.add_argument(
        "--cases", nargs="+", choices=tuple(DATASETS), default=tuple(DEFAULT_DATASETS)
    )
    return parser.parse_args()


def configure_publication_style():
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8,
            "axes.labelsize": 9,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7,
            "axes.linewidth": 0.8,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def load_datasets(data_dir, cases):
    datasets = {}
    for label in cases:
        filename = DATASETS[label]
        csv_path = data_dir / filename
        if not csv_path.is_file():
            raise FileNotFoundError(f"Cannot find required CSV: {csv_path}")

        frame = pd.read_csv(csv_path, usecols=[AIR2_COLUMN, T2_COLUMN, EPISODE_COLUMN])
        air2 = pd.to_numeric(frame[AIR2_COLUMN], errors="coerce").to_numpy()
        t2 = pd.to_numeric(frame[T2_COLUMN], errors="coerce").to_numpy()
        episodes = frame[EPISODE_COLUMN].to_numpy()
        finite = np.isfinite(air2) & np.isfinite(t2)
        if not finite.any():
            raise ValueError(f"No finite MV data found in {csv_path}")

        datasets[label] = (air2[finite], t2[finite], episodes[finite])
        print(f"Loaded {label}: {finite.sum()} points from {csv_path}")
    return datasets


def shared_axis_limits(datasets):
    all_air2 = np.concatenate([values[0] for values in datasets.values()])
    all_t2 = np.concatenate([values[1] for values in datasets.values()])
    x_limits = (
        min(100.0, np.floor(all_air2.min() / 10.0) * 10.0),
        max(350.0, np.ceil(all_air2.max() / 10.0) * 10.0),
    )
    y_limits = (
        min(100.0, np.floor(all_t2.min() / 10.0) * 10.0),
        max(300.0, np.ceil(all_t2.max() / 10.0) * 10.0),
    )
    return x_limits, y_limits


def case_axis_limits(label, datasets):
    if label in OOD_DATASETS:
        return OOD_LIMITS["air2" if label in AIR2_OOD_CASES else "t2"]
    return shared_axis_limits(datasets)


def draw_trajectory(ax, air2, t2, episodes, x_limits, y_limits, show_legend):
    episode_starts = np.r_[0, np.flatnonzero(episodes[1:] != episodes[:-1]) + 1]
    for start, end in zip(episode_starts, np.r_[episode_starts[1:], len(air2)]):
        ax.plot(
            air2[start:end],
            t2[start:end],
            color=TRAJECTORY_COLOR,
            linewidth=1.8,
            alpha=0.9,
            marker="o",
            markersize=1.2,
            markerfacecolor="#ADD8E6",
            markeredgecolor=TRAJECTORY_COLOR,
            markeredgewidth=0.2,
            zorder=2,
        )
    ax.scatter(
        air2[0],
        t2[0],
        s=30,
        color=START_COLOR,
        marker="o",
        edgecolor="black",
        linewidth=0.5,
        label="Start",
        zorder=4,
    )
    ax.scatter(
        air2[-1],
        t2[-1],
        s=30,
        color=END_COLOR,
        marker="s",
        edgecolor="black",
        linewidth=0.5,
        label="End",
        zorder=4,
    )

    start_on_right = air2[0] > sum(x_limits) / 2
    end_on_right = air2[-1] > sum(x_limits) / 2
    ax.annotate(
        f"Start\n({air2[0]:.1f}, {t2[0]:.1f})",
        (air2[0], t2[0]),
        xytext=(-7 if start_on_right else 7, 7),
        textcoords="offset points",
        ha="right" if start_on_right else "left",
        fontsize=6.5,
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": "#90EE90",
            "edgecolor": START_COLOR,
            "alpha": 0.9,
        },
        zorder=5,
    )
    ax.annotate(
        f"End\n({air2[-1]:.1f}, {t2[-1]:.1f})",
        (air2[-1], t2[-1]),
        xytext=(-7 if end_on_right else 7, -18),
        textcoords="offset points",
        ha="right" if end_on_right else "left",
        fontsize=6.5,
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": "#F08080",
            "edgecolor": END_COLOR,
            "alpha": 0.9,
        },
        zorder=5,
    )

    xmin, xmax, ymin, ymax = TRAINING_RANGE
    boundary_style = {
        "color": BOUNDARY_COLOR,
        "linewidth": 1.0,
        "linestyle": "--",
        "alpha": 0.85,
        "zorder": 1,
    }
    visible_x = [
        boundary for boundary in (xmin, xmax)
        if x_limits[0] <= boundary <= x_limits[1]
    ]
    for index, boundary in enumerate(visible_x):
        ax.axvline(
            boundary,
            label="Original X Range" if index == 0 else None,
            **boundary_style,
        )
        ax.text(
            boundary, y_limits[0] + 0.02 * (y_limits[1] - y_limits[0]),
            f"X={boundary:.0f}", rotation=90, fontsize=6.5,
            fontweight="bold", ha="right", va="bottom",
        )
    visible_y = [
        boundary for boundary in (ymin, ymax)
        if y_limits[0] <= boundary <= y_limits[1]
    ]
    for index, boundary in enumerate(visible_y):
        ax.axhline(
            boundary,
            label="Original Y Range" if index == 0 else None,
            **boundary_style,
        )
        ax.text(
            x_limits[0] + 0.02 * (x_limits[1] - x_limits[0]), boundary,
            f"Y={boundary:.0f}", fontsize=6.5, fontweight="bold",
            ha="left", va="bottom",
        )

    ax.set_xlim(*x_limits)
    ax.set_ylim(*y_limits)
    ax.set_xlabel(r"Air2 Flow Rate (m$^3$/h)")
    ax.set_ylabel(r"$T_2$ set point ($^\circ$C)")
    ax.grid(True, color="#D9D9D9", linewidth=0.45, alpha=0.65)
    ax.tick_params(direction="out", length=3)
    if show_legend:
        ax.legend(loc="upper right", frameon=True, handlelength=2.4)


def save_figure(fig, output_base):
    fig.savefig(output_base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(output_base.with_suffix(".png"), dpi=600, bbox_inches="tight")
    print(f"Saved {output_base.with_suffix('.pdf')}")
    print(f"Saved {output_base.with_suffix('.png')}")


def create_individual_figures(datasets, output_dir, show):
    for label, (air2, t2, episodes) in datasets.items():
        fig, ax = plt.subplots(figsize=(3.5, 3.0))
        individual_limits = case_axis_limits(label, {label: (air2, t2, episodes)})
        draw_trajectory(ax, air2, t2, episodes, *individual_limits, show_legend=True)
        fig.tight_layout(pad=0.4)
        save_figure(fig, output_dir / f"mv_trajectory_{label}")
        if show:
            plt.show()
        plt.close(fig)


def create_combined_figure(datasets, output_dir, x_limits, y_limits, show):
    columns = 2
    rows = math.ceil(len(datasets) / columns)
    focus_ood = tuple(datasets) == tuple(OOD_DATASETS)
    share = "col" if focus_ood else True
    fig, axes = plt.subplots(rows, columns, figsize=(7.2, 2.85 * rows), sharex=share, sharey=share)

    for index, (ax, (label, (air2, t2, episodes))) in enumerate(
        zip(axes.flat, datasets.items())
    ):
        limits = case_axis_limits(label, datasets) if focus_ood else (x_limits, y_limits)
        draw_trajectory(ax, air2, t2, episodes, *limits, show_legend=False)
        if index < (rows - 1) * columns:
            ax.set_xlabel("")
        if index % 2 == 1:
            ax.set_ylabel("")
        ax.text(
            0.98,
            0.97,
            f"({chr(97 + index)}) {label}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            fontweight="bold",
        )

    for ax in list(axes.flat)[len(datasets):]:
        ax.set_visible(False)

    handles, labels = [], []
    for ax in axes.flat:
        panel_handles, panel_labels = ax.get_legend_handles_labels()
        for handle, label in zip(panel_handles, panel_labels):
            if label not in labels:
                handles.append(handle)
                labels.append(label)
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.005),
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1), pad=0.6)
    output_name = (
        "mv_trajectory_R5_cases"
        if tuple(datasets) == tuple(DEFAULT_DATASETS)
        else "mv_trajectory_" + "_".join(datasets)
    )
    save_figure(fig, output_dir / output_name)
    if show:
        plt.show()
    plt.close(fig)


def main():
    args = parse_args()
    if args.no_show:
        plt.switch_backend("Agg")
    configure_publication_style()
    datasets = load_datasets(args.data_dir, args.cases)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    x_limits, y_limits = shared_axis_limits(datasets)

    show = not args.no_show
    create_individual_figures(datasets, args.output_dir, show)
    create_combined_figure(datasets, args.output_dir, x_limits, y_limits, show)


if __name__ == "__main__":
    main()
