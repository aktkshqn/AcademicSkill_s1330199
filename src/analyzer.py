# src/analyzer.py
import os
import csv

from .config import AUDIO_DIR, CSV_DIR, PLOT_DIR
from .f0_extractor import extract_f0
from .visualize import save_f0_plot
from .voicing import is_voiced_by_flag, is_voiced_by_f0
from .video import create_video

def analyze_file(path, subject, sample):
    # F0 と voiced_flag を取得
    f0, times, sr, voiced_flag = extract_f0(path)

    # CSV 出力
    csv_path = os.path.join(CSV_DIR, f"{subject}_{sample}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "f0", "is_voiced"])
        for t, fv, vf in zip(times, f0, voiced_flag):
            # voiced_flag は None だったり bool 配列で入る
            if vf is None:
                voiced = 1 if is_voiced_by_f0(fv) else 0
            else:
                voiced = 1 if is_voiced_by_flag(vf) else 0
            writer.writerow([f"{t:.4f}", f"{fv:.3f}", voiced])

    # 静的プロット（参考用PNG）
    image_path = save_f0_plot(subject, sample, times, f0)

    # 動画作成（F0軸データ・voiced_flag も渡す）
    mp4_path = create_video(times, f0, voiced_flag, path, subject, sample)

    return csv_path, image_path, mp4_path
