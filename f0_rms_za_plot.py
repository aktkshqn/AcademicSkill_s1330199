import librosa
import numpy as np
import os

# --- 設定パラメータ ---
WAV_FILE = 'sample1.wav'       # 分析したい音声ファイル名 (同じディレクトリに配置)
RMS_THRESHOLD = 0.01          # 音が存在するとみなすRMSのしきい値 (0.0～1.0)
F0_METHOD = 'pyin'            # F0抽出アルゴリズム (pyinが最もロバスト)
# --- 設定終わり ---

def analyze_voicing(file_path):
    """
    WAVファイルをロードし、F0とRMSを計算して、有声フレームの割合を出力します。
    """
    if not os.path.exists(file_path):
        print(f"[エラー] ファイルが見つかりません: {file_path}")
        return

    print(f"--- 音声ファイル分析: {file_path} ---")

    try:
        # 1. 音声データのロード
        y, sr = librosa.load(file_path, sr=None) 
        
        # hop_length: 分析の細かさ (フレームサイズ)。小さいほど詳細。
        HOP_LENGTH = 512
        
        # 2. 短時間エネルギー (RMS) の計算
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        
        # 3. 基本周波数 (f0) の計算
        f0, voiced_flag, voiced_probabilities = librosa.pyin(
            y, 
            fmin=librosa.note_to_hz('C2'),  # 65.4 Hz (男性の低音程度)
            fmax=librosa.note_to_hz('C6'),  # 1046.5 Hz (子どもの高音程度)
            sr=sr,
            hop_length=HOP_LENGTH
        )
        
        # f0の時間軸に合わせてRMSをリサンプリング (フレーム数を揃える)
        rms_resampled = librosa.util.fix_length(rms, size=len(f0)) 

    except Exception as e:
        print(f"  [致命的なエラー] データ処理中にエラーが発生しました: {e}")
        return

    # 4. 有音区間の特定
    # RMSがしきい値を超えているフレームを「有音区間」と定義します
    sound_frames = rms_resampled > RMS_THRESHOLD
    
    total_sound_frames = np.sum(sound_frames)

    if total_sound_frames == 0:
        print("  -> [結果] 有音区間が検出されませんでした。（音声が小さすぎるか、無音です）")
        return

    # 5. 有声/無声の判別
    
    # 有音区間（声が入っているフレーム）に絞ってf0データを取り出す
    f0_in_sound_frames = f0[sound_frames] 
    
    # f0が NaN (Not a Number) のフレームは「無声」と判定される
    unvoiced_frames = np.isnan(f0_in_sound_frames)
    
    # 有声フレーム数
    voiced_count = total_sound_frames - np.sum(unvoiced_frames)
    
    # 無声フレーム数
    unvoiced_count = np.sum(unvoiced_frames)

    # 6. 結果の出力
    
    print("-" * 30)
    print("### 📊 有声/無声 判別結果")
    print(f"  - 全フレーム数 (有音区間): {total_sound_frames} フレーム")
    print(f"  - 有声フレーム数 ($f_0$検出): {voiced_count} フレーム")
    print(f"  - 無声フレーム数 ($f_0$未検出): {unvoiced_count} フレーム")
    
    # 割合の計算
    voiced_ratio = (voiced_count / total_sound_frames) * 100
    unvoiced_ratio = (unvoiced_count / total_sound_frames) * 100
    
    print(f"  - 有声フレームの割合: {voiced_ratio:.2f}%")
    print(f"  - 無声フレームの割合: {unvoiced_ratio:.2f}%")
    print("-" * 30)
    
    if unvoiced_ratio > 50:
        print("  -> [判定] 音声の半分以上が無声です。全体として無声音が多い発話かもしれません。")
    elif unvoiced_ratio > 10:
        print("  -> [判定] 一部に無声区間があります。摩擦音や破裂音、または語尾の無声化の可能性があります。")
    else:
        print("  -> [判定] 非常に高い割合で有声です。（母音中心の継続音など）")


if __name__ == "__main__":
    # sample.wav を用意してから実行してください
    analyze_voicing(WAV_FILE)