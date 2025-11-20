import librosa
import numpy as np
import pandas as pd
import os
import re

# --- 設定パラメータ ---
ROOT_DIR = './output'  # 解析対象のフォルダのルートパス
OUTPUT_CSV = 'za_line_analysis_results.csv' # 結果を保存するCSVファイル名
RMS_THRESHOLD = 0.01   # 有音区間と見なすRMSのしきい値
F0_METHOD = 'pyin'     # F0抽出アルゴリズム
# --- 設定終わり ---

# ファイル名からメタデータを抽出するための正規表現パターン
# 例: S01_1_250_ざ.wav
FILENAME_PATTERN = re.compile(r'S(\d+)_(\d+)_(\d+)_([ざじずぜぞ])\.wav$')

def extract_metadata(filename):
    """ファイル名からメタデータ（被験者ID、音素など）を抽出する"""
    match = FILENAME_PATTERN.search(filename)
    if match:
        return {
            'subject_id': int(match.group(1)),
            'example_id': int(match.group(2)),
            'start_ms': int(match.group(3)),
            'phoneme': match.group(4)
        }
    return None

def analyze_audio_segment(file_path):
    """
    個別の音声ファイルを解析し、有声/無声、RMS平均値などの特徴量を抽出する
    """
    try:
        # 1. 音声データのロード (サンプリングレートは元のまま)
        y, sr = librosa.load(file_path, sr=None) 
        
        HOP_LENGTH = 512 # 分析の細かさ (フレーム移動量)
        
        # 2. 短時間エネルギー (RMS) の計算
        rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
        
        # 3. 基本周波数 (f0) の計算
        f0, voiced_flag, _ = librosa.pyin(
            y, 
            fmin=librosa.note_to_hz('C2'), 
            fmax=librosa.note_to_hz('C6'),
            sr=sr,
            hop_length=HOP_LENGTH
        )

    except Exception as e:
        # ロードや計算に失敗した場合は空の辞書を返す
        print(f"  [エラー] {file_path} の処理に失敗: {e}")
        return None

    # --- 特徴量計算 ---
    
    # 1. 有音区間の特定 (RMSがしきい値を超えているフレーム)
    sound_frames = rms > RMS_THRESHOLD
    total_sound_frames = np.sum(sound_frames)

    # 2. 有音区間における平均RMS
    mean_rms = np.mean(rms[sound_frames]) if total_sound_frames > 0 else 0.0
    
    # 3. 有声/無声の判別
    # f0の時間軸に合わせてRMSをリサンプリング (フレーム数を揃える)
    rms_resampled = librosa.util.fix_length(rms, size=len(f0)) 
    sound_frames_f0 = rms_resampled > RMS_THRESHOLD
    
    f0_in_sound_frames = f0[sound_frames_f0] 
    
    # f0が NaN (Not a Number) のフレームは「無声」
    unvoiced_frames_count = np.sum(np.isnan(f0_in_sound_frames))
    
    # 有声フレーム数
    voiced_count = total_sound_frames - unvoiced_frames_count
    
    # 全有音区間に対する有声フレームの割合
    voiced_ratio = (voiced_count / total_sound_frames) if total_sound_frames > 0 else 0.0

    # 4. 有声/無声の最終判定 (割合が50%を超えていれば有声とみなす)
    voicing_decision = 'Voiced' if voiced_ratio >= 0.5 else 'Unvoiced'

    # 5. f0の平均値 (有声区間のみ)
    # NaNを除外して平均を計算
    f0_mean_voiced = np.nanmean(f0_in_sound_frames) if np.sum(~np.isnan(f0_in_sound_frames)) > 0 else 0.0

    return {
        'total_duration_s': len(y) / sr,
        'mean_rms': mean_rms,
        'f0_mean_voiced_hz': f0_mean_voiced,
        'voiced_ratio': voiced_ratio,
        'voicing_decision': voicing_decision,
        'total_sound_frames': total_sound_frames,
        'unvoiced_frames_count': unvoiced_frames_count
    }

def process_all_files(root_dir):
    """ルートディレクトリ以下の全てのWAVファイルを走査し、解析を実行する"""
    results = []
    
    # os.walkでサブフォルダも含めて全てのファイルを走査
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.wav'):
                file_path = os.path.join(dirpath, filename)
                
                # 1. メタデータ抽出
                metadata = extract_metadata(filename)
                
                # ファイル名解析が失敗した場合はスキップ
                if metadata is None:
                    print(f"  [スキップ] ファイル名パターン不一致: {file_path}")
                    continue
                
                # 2. 音声データ解析
                audio_features = analyze_audio_segment(file_path)

                if audio_features is not None:
                    # 3. メタデータと特徴量を結合してリストに追加
                    full_data = {**metadata, **audio_features, 'full_filename': filename}
                    results.append(full_data)
                    print(f"  [完了] {filename}: 判定={full_data['voicing_decision']}, f0={full_data['f0_mean_voiced_hz']:.1f}Hz")
                
    return pd.DataFrame(results)

if __name__ == "__main__":
    if not os.path.exists(ROOT_DIR):
        print(f"ルートディレクトリが見つかりません: {ROOT_DIR}")
        print("解析を開始する前に、'./output' フォルダを作成し、その中にサブフォルダを配置してください。")
    else:
        print(f"### 解析開始: {ROOT_DIR} 以下の全WAVファイル")
        
        # 全ファイル処理
        df_results = process_all_files(ROOT_DIR)

        # 結果をCSVに出力
        if not df_results.empty:
            df_results.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
            print("-" * 50)
            print(f"✅ 解析完了！結果は {OUTPUT_CSV} に保存されました。")
            print(f"総ファイル数: {len(df_results)} 件")
        else:
            print("解析対象のファイルが見つかりませんでした。")