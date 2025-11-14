# src/f0_extractor.py
import numpy as np
import librosa

# 共通 hop_length を決めておくと時間軸が安定します
HOP_LENGTH = 256
FRAME_LENGTH = 2048

def extract_f0(path):
    """
    return: f0 (Hz, np.array), times (sec, np.array), sr (int), voiced_flag (bool array)
    """
    y, sr = librosa.load(path, sr=None)

    # pyin の戻り値: f0, voiced_flag, voiced_prob
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=70,
        fmax=400,
        sr=sr,
        frame_length=FRAME_LENGTH,
        hop_length=HOP_LENGTH
    )

    # NaN を 0 に置き換える（プロットやCSV用）／ただし voiced_flag を有効利用
    f0_clean = np.where(np.isnan(f0), 0.0, f0)

    # 時間軸: フレームインデックス -> 時間
    frames = np.arange(len(f0_clean))
    times = librosa.frames_to_time(frames, sr=sr, hop_length=HOP_LENGTH)

    return f0_clean, times, sr, voiced_flag
