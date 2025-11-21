import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
import sys

# --- 1. 設定 ---
INPUT_ROOT_DIR = "wav"  # WAVファイルがあるルートディレクトリ
OUTPUT_ROOT_DIR = "output" # 結果を保存する大元のフォルダ

# ⚠️ 話者IDリスト: 処理したい話者ID
SPEAKER_IDS = ["01", "02", "03"]

# 例文データ
SENTENCES_DATA = [
    {"id": "001", "text": "ざるそばやのまちじかんにじっくりざっしをよんでいた。"},
    {"id": "002", "text": "いちにちじゅうずっとざーざーふりでざんねんだった。"},
    {"id": "003", "text": "ぞんざいにざっしをよんでたら、ざつなあつかいをちゅういされた。"},
    {"id": "004", "text": "ぜんぶのじゅぎょうがおわったら、じゅうぶんなじかんがとれる。"},
    {"id": "005", "text": "ぞうをじっくりみていたら、ざんねんながらじかんがなくなった。"},
    {"id": "006", "text": "じゅぎょうじかんはねていたら、ぜんぜんしらないもんだいばかり。"},
    {"id": "007", "text": "おそうざいのせーるじかんはずいぶんこんざつしていた。"},
    {"id": "008", "text": "じかんをはかって、ぜんぶのもんだいをざっとといてみた。"},
    {"id": "009", "text": "ぞんぶんにあそんだあと、ざっくりかたづけをしてじかんどおりにかえった。"},
    {"id": "010", "text": "ずっとじょうだんをいいあいたいが、ざんねんながらもうじかん。"},
]

# ざ行などのフォルダマッピング
Z_LINE_MAP = {
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'ガ': 'ga', 'ギ': 'gi', 'グ': 'gu', 'ゲ': 'ge', 'ゴ': 'go',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ダ': 'da', 'ヂ': 'di', 'ヅ': 'du', 'デ': 'de', 'ド': 'do', 
    'パ': 'pa', 'ピ': 'pi', 'プ': 'pu', 'ペ': 'pe', 'ポ': 'po', 
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
}
OTHER_DIR = "other"

# --- 2. マージン設定 ---
# ざ行の文字に前後にどれだけマージン（余裕）を追加するか (ミリ秒)
MARGIN_MS = 50 

# --- 3. 無音除去の設定 ---
# 無音とみなすレベル (dBFS)。平均音量からの相対値で使用します。
# 例: 平均より -16dB 小さい音を無音とするなど
SILENCE_THRESH_OFFSET = -16 
# 無音とみなす最小の長さ (ミリ秒)。これより短い無音は無視（発話の一部とみなす）
MIN_SILENCE_LEN_MS = 500

# --- 4. 関数定義 ---

def categorize_char(char):
    """文字をフォルダ名に分類"""
    if char in Z_LINE_MAP:
        return Z_LINE_MAP[char]
    return OTHER_DIR

def remove_silence(audio_segment):
    """
    音声データから無音区間を除去して、発話部分だけを繋げた音声を返す。
    """
    # 音声の平均音量 (dBFS) を取得
    audio_level = audio_segment.dBFS
    
    # 無音のしきい値を決定 (平均音量 - オフセット)
    # 固定値 (-40dBFSなど) ではなく、録音レベルに合わせて動的に設定
    silence_thresh = audio_level + SILENCE_THRESH_OFFSET
    
    # split_on_silence で無音部分で分割された音声のリストを取得
    # keep_silence=100 は、分割点の前後100msの無音を残す（自然に聞こえるように）
    chunks = split_on_silence(
        audio_segment,
        min_silence_len=MIN_SILENCE_LEN_MS,
        silence_thresh=silence_thresh,
        keep_silence=100 
    )
    
    if not chunks:
        return None

    # 分割されたチャンクを結合して一つの音声にする
    processed_audio = chunks[0]
    for chunk in chunks[1:]:
        processed_audio += chunk
        
    return processed_audio

def segment_audio_batch(input_root, output_root, speaker_ids, sentences_data):
    print(f"処理開始: {len(speaker_ids)}名 x {len(sentences_data)}例文")
    
    for speaker_id in speaker_ids:
        for sentence in sentences_data:
            sentence_id = sentence['id']
            text = sentence['text']
            chars = list(text) # 文字リストに分解

            # 入力ファイルパス
            input_filename = f"S{speaker_id}_{sentence_id}.wav"
            input_path = os.path.join(input_root, input_filename)

            if not os.path.exists(input_path):
                print(f"[スキップ] ファイルなし: {input_path}")
                continue

            print(f"\n--- 解析中: {input_filename} ---")
            
            try:
                # 1. 音声ロード
                original_audio = AudioSegment.from_wav(input_path)
                
                # 2. 無音除去 (前後の無音や、途中の長い無音をカット)
                audio = remove_silence(original_audio)
                
                if audio is None:
                    print("  [警告] 音声データが全て無音と判定されました。")
                    continue

                total_duration_ms = len(audio)
                
                # 3. 1文字あたりの時間を計算 (等分割)
                duration_per_char_ms = total_duration_ms / len(chars)
                print(f"  有効時間: {total_duration_ms/1000:.2f}秒, 文字数: {len(chars)}, 1文字平均: {duration_per_char_ms:.1f}ms")

                # 4. 切り出し処理
                current_time_ms = 0
                
                for i, char in enumerate(chars):
                    category_dir = categorize_char(char)
                    
                    # 基本の切り出し区間 (等分割)
                    start_base = current_time_ms
                    end_base = current_time_ms + duration_per_char_ms
                    
                    # ターゲット文字（ざ行など）の場合はマージンを追加
                    if category_dir != OTHER_DIR:
                        start_final = max(0, start_base - MARGIN_MS)
                        end_final = min(total_duration_ms, end_base + MARGIN_MS)
                    else:
                        start_final = start_base
                        end_final = end_base

                    # 保存先の準備
                    # フォルダ構成: output/za/S01_001_05_ざ.wav
                    save_dir = os.path.join(output_root, category_dir)
                    os.makedirs(save_dir, exist_ok=True)
                    
                    # ファイル名: S{話者}_{例文ID}_{文字順}_{文字}.wav
                    # i+1 で1始まりの番号にする (01, 02...)
                    save_filename = f"S{speaker_id}_{sentence_id}_{i+1:02d}_{char}.wav"
                    save_path = os.path.join(save_dir, save_filename)
                    
                    # 切り出して保存
                    segment = audio[int(start_final):int(end_final)]
                    segment.export(save_path, format="wav")
                    
                    # ざ行の時だけログ出し
                    if category_dir != OTHER_DIR:
                        print(f"    -> 保存: {category_dir}/{save_filename} ({len(segment)}ms)")

                    # 次の文字へ (時間はベースの時間で進める)
                    current_time_ms = end_base

            except Exception as e:
                print(f"  [エラー] 処理中に問題が発生しました: {e}")

if __name__ == "__main__":
    # フォルダの存在確認
    if not os.path.exists(INPUT_ROOT_DIR):
        print(f"[エラー] 入力フォルダ '{INPUT_ROOT_DIR}' が見つかりません。作成してWAVファイルを入れてください。")
    else:
        segment_audio_batch(INPUT_ROOT_DIR, OUTPUT_ROOT_DIR, SPEAKER_IDS, SENTENCES_DATA)
        print("\n✅ 全ての処理が完了しました。")