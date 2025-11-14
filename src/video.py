# src/video.py
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # 描画バックエンド固定
import matplotlib.pyplot as plt
from moviepy.editor import VideoClip, AudioFileClip
from .config import VIDEO_DIR

# 出力解像度（必要に応じて変更）
W, H = 1280, 720
DPI = 100

def create_video(times, f0, voiced_flag, audio_path, subject, sample):
    """
    times: np.array (seconds)
    f0: np.array (Hz)
    voiced_flag: iterable of bools (same length)
    audio_path: path to wav
    """

    # Load audio
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Prepare static plot data bounds
    ymin = 0
    ymax = max(100, np.max(f0) * 1.1)

    # Precompute for faster access
    times = np.array(times)
    f0 = np.array(f0)
    voiced_flag = np.array([bool(v) for v in voiced_flag])

    # Matplotlib figure (we render per-frame into numpy array)
    def make_frame(t):
        # t: current time in seconds
        fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
        ax = fig.add_axes([0.07, 0.2, 0.86, 0.7])  # main plot area

        # Plot full F0 curve (background)
        ax.plot(times, f0, linewidth=1.0, zorder=1)
        ax.set_xlim(0, max(duration, times[-1] if len(times) else duration))
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel("時間 (秒)")
        ax.set_ylabel("F0 (Hz)")
        ax.set_title(f"F0 推移（{subject} / {sample}）")

        # Draw cursor at current time
        ax.axvline(x=t, color="red", linewidth=1.2, zorder=3)

        # Show a small marker for the nearest frame value
        idx = np.searchsorted(times, t)
        if idx >= len(times):
            idx = len(times) - 1
        if idx < 0:
            idx = 0
        current_f0 = float(f0[idx]) if len(f0) else 0.0
        current_voiced = bool(voiced_flag[idx]) if len(voiced_flag) else False

        # draw marker
        ax.scatter([times[idx]], [current_f0], s=30, color="orange", zorder=4)

        # Text area below: show current time / f0 / voiced
        txt_ax = fig.add_axes([0.07, 0.02, 0.86, 0.15])
        txt_ax.axis("off")
        txt = (
            f"時刻: {t:.3f} s    "
            f"F0: {current_f0:.2f} Hz    "
            f"有声音: {'Yes' if current_voiced else 'No'}"
        )
        txt_ax.text(0.01, 0.5, txt, fontsize=14, va="center")

        # Render figure to RGB array
        fig.canvas.draw()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype="uint8")
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        plt.close(fig)
        return img

    # Create VideoClip using the make_frame function
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_audio(audio)

    output = os.path.join(VIDEO_DIR, f"{subject}_{sample}.mp4")

    # write_videofile: 指定 codec と audio_codec を指定
    clip.write_videofile(
        output,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        verbose=False,
        logger=None
    )

    return output
