# src/video.py
import os
import numpy as np
import matplotlib.pyplot as plt
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from .config import VIDEO_DIR

def create_video(image_path, audio_path, subject, sample, fps=30):
    """
    f0グラフと音声を時間同期した動画を作成（moviepy v2 対応）
    """
    # 音声ファイルを読み込み
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration  # 音声の長さ（秒）

    # f0グラフ画像を読み込み（matplotlib の imread を使用）
    f0_image = plt.imread(image_path)

    # NumPy 配列が float のときは 0-1 -> 0-255 uint8 に変換
    if np.issubdtype(f0_image.dtype, np.floating):
        f0_image = (np.clip(f0_image, 0.0, 1.0) * 255).astype(np.uint8)

    # フレーム数を計算（fps に基づく）
    total_frames = max(1, int(round(duration * fps)))

    # 同じ静止画を繰り返してフレーム列を作る
    frames = [f0_image] * total_frames

    # ImageSequenceClip を作成（duration はフレーム数/fps で自動設定される）
    video_clip = ImageSequenceClip(frames, fps=fps)

    # 音声を付与
    video_clip = video_clip.set_audio(audio_clip)

    # 出力先を作成して保存
    os.makedirs(VIDEO_DIR, exist_ok=True)
    out_path = os.path.join(VIDEO_DIR, f"{subject}_{sample}.mp4")

    video_clip.write_videofile(out_path, fps=fps, verbose=False)

    # リソース解放
    try:
        video_clip.close()
    except Exception:
        pass
    try:
        audio_clip.close()
    except Exception:
        pass

    return out_path
