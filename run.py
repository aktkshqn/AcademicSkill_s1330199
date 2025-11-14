import os
import re
from src.analyzer import analyze_file
from src.config import AUDIO_DIR

def main():
    pattern = re.compile(r"(S\d{2})_(\d{3})\.wav")

    for fname in os.listdir(AUDIO_DIR):
        m = pattern.match(fname)
        if not m:
            continue

        subject = m.group(1)
        sample = m.group(2)
        path = os.path.join(AUDIO_DIR, fname)

        print(f"--- 処理: {fname} ---")

        try:
            csv_path, img_path, mp4_path = analyze_file(path, subject, sample)
            print("✓ CSV:", csv_path)
            print("✓ PNG:", img_path)
            print("✓ MP4:", mp4_path)
        except Exception as e:
            print(f"✗ エラー: {e}")

if __name__ == "__main__":
    main()