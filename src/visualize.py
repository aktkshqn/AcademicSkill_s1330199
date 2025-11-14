# src/visualize.py
import matplotlib.pyplot as plt
from .config import PLOT_DIR
import os
plt.rcParams["font.family"] = "Yu Gothic"

def save_f0_plot(subject, sample, times, f0):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, f0, linewidth=1.0)
    ax.set_xlabel("時間 (秒)")
    ax.set_ylabel("F0 (Hz)")
    ax.set_title(f"F0 推移（{subject} / {sample}）")

    path = os.path.join(PLOT_DIR, f"{subject}_{sample}_f0.png")
    fig.savefig(path)
    plt.close(fig)
    return path
