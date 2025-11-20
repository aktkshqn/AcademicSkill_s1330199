# src/analyzer.py
import os
import csv

from .config import AUDIO_DIR, CSV_DIR, PLOT_DIR, USE_VIDEO
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

    # 静的プロット（PNG）
    image_path = save_f0_plot(subject, sample, times, f0)

    # 動画は設定が有効な場合のみ試みる（失敗しても例外で止めない）
    mp4_path = None
    if USE_VIDEO:
        try:
            mp4_path = create_video(times, f0, voiced_flag, path, subject, sample)
        except Exception as e:
            # 動画作成失敗は通知して続行
            print(f"[警告] 動画作成に失敗しました。動画をスキップします: {e}")
            mp4_path = None

    return csv_path, image_path, mp4_path
