import os

# データパス
AUDIO_DIR = "./wav"

OUTPUT_ROOT = "./output"
CSV_DIR = os.path.join(OUTPUT_ROOT, "csv")
PLOT_DIR = os.path.join(OUTPUT_ROOT, "plots")
VIDEO_DIR = os.path.join(OUTPUT_ROOT, "video")

# 出力フォルダ作成
for d in [CSV_DIR, PLOT_DIR, VIDEO_DIR]:
    os.makedirs(d, exist_ok=True)

# F0有声音判定の閾値
F0_THRESHOLD = 80
