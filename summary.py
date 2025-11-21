import pandas as pd
import numpy as np
import os

# --- 設定パラメータ ---
INPUT_CSV = 'za_line_analysis_results.csv'
OUTPUT_CSV = 'nationality_summary_comparison.csv' # 出力ファイルをCSVに変更
JAPANESE_ID_THRESHOLD = 3 # subject_idが3以上のデータを日本人と分類
# --- 設定終わり ---

def create_nationality_comparison_tables(csv_file):
    """
    CSVを読み込み、被験者IDに基づき国籍を分類し、
    RMSゼロ除外後の有効データのみで国籍別の音素別集計テーブルを作成する。
    """
    print("### 📊 国籍別比較集計の開始")
    
    try:
        # データの読み込み（文字化け対策のため、ここでは'utf-8'で試行）
        df = pd.read_csv(csv_file, encoding='utf-8')
    except Exception:
        # utf-8で失敗した場合、日本の標準的なエンコーディングである'shift_jis'または'cp932'を試す
        try:
            df = pd.read_csv(csv_file, encoding='shift_jis')
        except Exception:
            print("[エラー] CSVファイルの読み込みに失敗しました。エンコーディング（utf-8, shift_jis）を確認してください。")
            return
            
    # 1. 国籍の分類
    # subject_idが設定値以上 (>= 3) なら Japanese、それ以外は Korean と分類する新しい列を作成
    df['nationality'] = np.where(df['subject_id'] >= JAPANESE_ID_THRESHOLD, 'Japanese', 'Korean')
    
    print(f" -> データ総行数: {len(df)} 行")
    print(f" -> subject_id {JAPANESE_ID_THRESHOLD} 以上を日本人、それ以外を韓国人として分類しました。")
    
    # 2. RMSゼロデータの除外（有効な発話データのみに限定）
    df_valid = df[df['total_sound_frames'] > 0].copy()
    print(f" -> RMSゼロ除外後の有効データ総数: {len(df_valid)} 行")

    if df_valid.empty:
        print(" [結果] 有効な発話データが残っていません。")
        return

    # 3. 有声/無声の判断を数値化 (Voiced=1, Unvoiced=0)
    df_valid['is_voiced'] = np.where(df_valid['voicing_decision'] == 'Voiced', 1, 0)
    df_valid['is_unvoiced'] = np.where(df_valid['voicing_decision'] == 'Unvoiced', 1, 0)
    
    # ----------------------------------------------------
    # 集計ヘルパー関数
    # ----------------------------------------------------
    def generate_summary_by_group(data_frame, group_name):
        """指定された国籍のデータに対し、音素ごとの集計を行う"""
        
        # 1. 音素でグループ化し、Voiced/Unvoicedの数を集計
        summary = data_frame.groupby('phoneme').agg(
            total_count=('full_filename', 'count'), 
            voiced_count=('is_voiced', 'sum'),      
            unvoiced_count=('is_unvoiced', 'sum')   
        ).reset_index()

        # 2. 無声率の計算
        summary['unvoiced_rate'] = (summary['unvoiced_count'] / summary['total_count']) * 100
        summary['unvoiced_rate'] = summary['unvoiced_rate'].round(2)
        
        # 3. 最終的な整形
        final_table = summary[['phoneme', 'voiced_count', 'unvoiced_count', 'unvoiced_rate']]
        
        # カラム名に国籍名を付与
        final_table.columns = [
            '音素', 
            f'{group_name}_有声数', 
            f'{group_name}_無声数', 
            f'{group_name}_無声率(%)'
        ]
        
        # '音素'をインデックス（行名）として設定
        final_table = final_table.set_index('音素')

        print(f" -> {group_name} の集計データを準備しました。")
        return final_table

    # ----------------------------------------------------
    # メイン集計とCSV出力
    # ----------------------------------------------------
    
    # 国籍ごとにデータを分割
    df_korean = df_valid[df_valid['nationality'] == 'Korean']
    df_japanese = df_valid[df_valid['nationality'] == 'Japanese']

    # 1. 韓国人グループの集計
    table_korean = generate_summary_by_group(df_korean, "韓国人")

    # 2. 日本人グループの集計
    table_japanese = generate_summary_by_group(df_japanese, "日本人")

    # 3. 2つの集計結果を結合して一つの比較テーブルを作成
    comparison_table = pd.merge(
        table_korean, 
        table_japanese, 
        left_index=True, 
        right_index=True, 
        how='outer' # どちらかの音素データがない場合でも結合
    )
    
    # 4. CSVに出力 (文字化けしないよう UTF-8 で出力し、インデックス（音素名）を出力する)
    try:
        comparison_table.to_csv(OUTPUT_CSV, encoding='utf-8', index=True)
    except Exception as e:
        print(f"[エラー] CSVファイル '{OUTPUT_CSV}' の書き出し中にエラーが発生しました: {e}")
        return
    
    print("-" * 50)
    print(f"✅ 処理完了！国籍別比較結果はCSVファイル '{OUTPUT_CSV}' に保存されました。")
    print(" 音素（ざ, じ, ず, ぜ, ぞ）ごとの有声数、無声数、無声率が並んでいます。")

if __name__ == "__main__":
    create_nationality_comparison_tables(INPUT_CSV)