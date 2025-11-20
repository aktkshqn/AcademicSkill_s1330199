import os
from pydub import AudioSegment

# --- 1. 設定 ---
INPUT_ROOT_DIR = "."  # WAVファイルがあるルートディレクトリ (例: "./wav")
OUTPUT_ROOT_DIR = "output" # 全ての結果を保存する大元のフォルダ

# ⚠️ 話者IDリスト: 処理したい話者IDをここに記述してください。
# 例: 協力者3人（ID: 01, 02, 03）の場合
SPEAKER_IDS = ["01", "02", "03"]

# 例文とそのIDのデータ (ファイル名生成のベースとなります)
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

# ざ行の文字と対応するフォルダ名のマッピング
Z_LINE_MAP = {
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    # 濁点を持つ全ての文字（カタカナ含む）にも対応させる場合はここに追加
    'ガ': 'ga', 'ギ': 'gi', 'グ': 'gu', 'ゲ': 'ge', 'ゴ': 'go',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ダ': 'da', 'ヂ': 'di', 'ヅ': 'du', 'デ': 'de', 'ド': 'do', 
    'パ': 'pa', 'ピ': 'pi', 'プ': 'pu', 'ペ': 'pe', 'ポ': 'po', # 半濁点もついでに追加
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
}
OTHER_DIR = "other"

# --- 2. マージン設定 ---
# ざ行の文字に前後にどれだけマージン（余裕）を追加するか (ミリ秒)
# 例: 50msだと、前後に50msずつ、合計100ms長く切り出されます。
MARGIN_MS = 50 

# --- 3. 分類ロジック ---
def categorize_char(char):
    """
    文字をざ行のフォルダ名に分類します。（カタカナ対応強化）
    """
    # ざ行のひらがなをチェック
    if char in Z_LINE_MAP:
        return Z_LINE_MAP[char]
    
    # 濁点・半濁点付きのカタカナをひらがなに戻してチェック (簡易的な分類)
    # ここでは、Z_LINE_MAPにない文字は全てOTHER_DIRになります。
    
    # 長音符 'ー' や句読点、促音 'っ' などは 'other' に分類されます
    return OTHER_DIR

# --- 4. メイン処理 ---
def simple_segment_audio_batch(input_root, output_root, speaker_ids, sentences_data):
    """
    複数の音声ファイルを一律時間分割で処理し、指定フォルダに分類して保存します。
    ざ行の文字については、前後にマージンを追加して切り出します。
    """
    if not speaker_ids or not sentences_data:
        print("エラー: 処理対象の話者IDまたは例文リストが空です。")
        return

    print(f"処理対象の話者数: {len(speaker_ids)}人, 例文数: {len(sentences_data)}種類")
    
    # 話者IDと例文IDを組み合わせる二重ループ
    for speaker_id in speaker_ids:
        for sentence in sentences_data:
            sentence_id = sentence['id']
            text = sentence['text']

            # ファイル名を生成: 例: S01_001.wav
            input_filename = f"S{speaker_id}_{sentence_id}.wav"
            input_path = os.path.join(input_root, input_filename)
            chars = list(text)

            print(f"\n--- 処理開始: [話者{speaker_id}, 例文{sentence_id}] ({input_filename}) ---")

            if not os.path.exists(input_path):
                print(f"警告: ファイル '{input_path}' が見つかりません。スキップします。")
                continue

            try:
                audio = AudioSegment.from_wav(input_path)
                total_duration_ms = len(audio)
                
                # 各文字が占める基本時間 (ミリ秒)
                duration_per_char_ms = total_duration_ms / len(chars)
                
                print(f"総時間: {total_duration_ms / 1000:.2f} 秒, 1文字あたり(ベース): {duration_per_char_ms:.2f} ms")

                current_time_ms = 0
                
                # 切り出しと保存
                for i, char in enumerate(chars):
                    # 分類フォルダを決定
                    category_dir = categorize_char(char)
                    
                    # 基本の区間
                    start_ms_base = current_time_ms
                    end_ms_base = current_time_ms + duration_per_char_ms
                    
                    # ざ行（濁点文字）の場合、マージンを追加して切り出し区間を広げる
                    if category_dir != OTHER_DIR:
                        # ざ行の切り出し区間を拡張
                        start_ms_final = max(0, start_ms_base - MARGIN_MS)
                        end_ms_final = min(total_duration_ms, end_ms_base + MARGIN_MS)
                    else:
                        # その他の文字は基本区間のまま
                        start_ms_final = start_ms_base
                        end_ms_final = end_ms_base
                    
                    # 出力パスを作成: output/category/S01_001_01_ざ.wav
                    output_sub_dir = os.path.join(output_root, category_dir)
                    os.makedirs(output_sub_dir, exist_ok=True) # フォルダがなければ作成
                    
                    # ファイル名に話者ID, 例文ID, 文字番号を含める
                    output_filename = f"S{speaker_id}_{sentence_id}_{i+1:02d}_{char}.wav"
                    output_path = os.path.join(output_sub_dir, output_filename)

                    # 音声をミリ秒単位で切り出し、保存
                    segment = audio[int(start_ms_final):int(end_ms_final)]
                    segment.export(output_path, format="wav")
                    
                    # 進捗を表示 (ざ行のみ詳細を表示)
                    if category_dir != OTHER_DIR:
                        print(f" -> {category_dir}に保存: {output_filename} (拡張: +{MARGIN_MS}ms/-{MARGIN_MS}ms)")
                    
                    # 次の文字の開始点は、常にベースの分割時間に基づいて移動
                    current_time_ms = end_ms_base 
                
                print(f"✅ {input_filename} の処理が完了しました。")

            except FileNotFoundError:
                print("\n🚨 エラー: ffmpegが見つからないか、音声ファイルの形式に問題があります。")
                print("    'pydub'の実行には、外部ツール 'ffmpeg' が必要です。インストールを確認してください。")
            except Exception as e:
                print(f"\n致命的なエラーが発生しました: {e}")


if __name__ == "__main__":
    simple_segment_audio_batch(INPUT_ROOT_DIR, OUTPUT_ROOT_DIR, SPEAKER_IDS, SENTENCES_DATA)