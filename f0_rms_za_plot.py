# f0_rms_za_plot.py
import os
import numpy as np
import librosa
import matplotlib.pyplot as plt
from aeneas.executetask import ExecuteTask
from aeneas.task import Task

# 入力ディレクトリ
AUDIO_DIR = "wav"
TEXT_FILE = "例文.txt"
OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ざ行判定用関数
def is_za_line(text):
    return any(c in "ざじずぜぞ" for c in text)

# 音素タイミング取得（aeneasで行単位）
def align_text(audio_path, text_line):
    config_string = "task_language=ja|is_text_type=plain|os_task_file_format=json"
    task = Task(config_string=config_string)
    task.audio_file_path_absolute = audio_path
    task.text_file_path_absolute = text_line
    task.output_file_path_absolute = "temp.json"
    ExecuteTask(task).execute()
    task.output_sync_map_file()
    # JSON 解析でざ行区間を取得するのは後で行う
    return task.output_file_path_absolute

def plot_f0_rms_with_za(audio_path, za_segments, output_name=None):
    y, sr = librosa.load(audio_path, sr=None)
    frame_length = 2048
    hop_length = 256

    # F0
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y, fmin=70, fmax=400, sr=sr, frame_length=frame_length, hop_length=hop_length
    )
    f0_clean = np.where(np.isnan(f0), 0.0, f0)
    times_f0 = librosa.frames_to_time(np.arange(len(f0_clean)), sr=sr, hop_length=hop_length)

    # RMS
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    rms_scaled = rms * (f0_clean.max() * 1.2 / rms.max() if rms.max() > 0 else 1.0)

    # プロット
    plt.figure(figsize=(12, 5))
    plt.plot(times_f0, f0_clean, color="red", label="F0 (Hz)")
    plt.fill_between(rms_times, 0, rms_scaled, color="lightblue", alpha=0.5, label="RMS (scaled)")

    # ざ行タイムハイライト
    for start, end in za_segments:
        plt.axvspan(start, end, color="lightgreen", alpha=0.3)

    plt.xlabel("時間 [秒]")
    plt.ylabel("F0 [Hz] / RMS（スケーリング済み）")
    plt.title(os.path.basename(audio_path))
    plt.legend()
    plt.tight_layout()

    if output_name is None:
        output_name = os.path.splitext(os.path.basename(audio_path))[0] + "_f0_rms_za.png"
    output_path = os.path.join(OUTPUT_DIR, output_name)
    plt.savefig(output_path)
    plt.close()
    print(f"出力完了: {output_path}")
    return output_path

# 実行例
if __name__ == "__main__":
    # 例文を読み込む
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for audio_file in os.listdir(AUDIO_DIR):
        if not audio_file.lower().endswith(".wav"):
            continue
        audio_path = os.path.join(AUDIO_DIR, audio_file)

        # 簡易: 行ごとにざ行を判定して、タイミングは wav 全体を均等に割り当てる（簡易版）
        duration = librosa.get_duration(filename=audio_path)
        n_lines = len(lines)
        za_segments = []
        for i, line in enumerate(lines):
            if is_za_line(line):
                start = duration * i / n_lines
                end = duration * (i + 1) / n_lines
                za_segments.append((start, end))

        plot_f0_rms_with_za(audio_path, za_segments)
