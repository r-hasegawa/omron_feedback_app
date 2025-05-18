import os
import sys
import numpy as np
import pandas as pd
import glob
import preprocessing

def correction_from_1min_data(filename):
    """
    filename：10秒METsのCSVファイル名　= [ユーザ名]10SECMETS_[日付].csv
    このファイル名から1分METsのCSVファイル名を取得し、ゼロ補正を行う

    """

    filename2 = filename.replace("10SECMETS", "METS")
    try:
        data_1min = pd.read_csv(filename2, encoding='utf-8', skiprows=3) 
    except UnicodeDecodeError:
        data_1min = pd.read_csv(filename2, encoding='shift_jis', skiprows=3) 
    frame = data_1min.iloc[:,0]
    data_1min_array = np.array(data_1min.iloc[:,1])

    # 閾値の決定
    optim_th = preprocessing.optimTh(data_1min_array)

    # ①0→1 補正 (前後60分間で1が出現する確率が閾値を超えるかどうか)
    corrected_prob = preprocessing.zeroProb(data_1min_array, 60, optim_th, 0)

    # ②1→0 補正 (10分以上0が続いていた場合は 0のままで1に補正しない)
    # 0が10以上続いた区間を0、それ以外を1とした配列が出力される
    corrected_consec_binary = preprocessing.zeroConsec(data_1min_array)

    # 合成 (①で0を1に補正するが、②に該当する場合は0に戻す ※②でもともと1の場所が0になることはなく、0になるのは必ず①で補正された場所)
    synth_data = preprocessing.zeroSynth(corrected_prob, corrected_consec_binary)

    # ここから10秒値のデータにアップサンプリング
    # データは直前の値で埋める (例えば0:00:10から0:00:50までのデータは0:00:00のデータで埋める)
    data_1min["synth_data"] = synth_data
    data_1min['synth_data'] = np.where(data_1min['synth_data'] > 0, 1.0, 0.0) # 0より位大きい場合1、それ以外の場合0の2値化する
    data_1min["時刻"] = pd.to_datetime(data_1min["時刻"], format="%H:%M:%S").dt.time
    new_time_range = pd.date_range("00:00:00", "23:59:50", freq="10s").time # 新しい時刻の範囲を生成（10秒刻み）
    expanded_df = pd.DataFrame({"時刻": new_time_range}) # 新しいDataFrameを作成
    expanded_df = expanded_df.merge(data_1min, on="時刻", how="left").ffill() # 元のデータを10秒刻みのデータにマージし、直前の値で補完
    # expanded_df["時刻"] = expanded_df["時刻"].dt.strftime('%H:%M:%S') # 時刻を再度文字列形式に変換
    expanded_df["時刻"] = expanded_df["時刻"].astype(str)

    return expanded_df



def process_csv_files(directory, correction="あり"):
    """
    指定されたディレクトリ内の「10SECMETS_」で終わるCSVファイルを読み取り、
    日付、最大値、最小値、平均、合計を含むサマリデータを生成します。
    """
    summary_data = []
    
    # 「*_10SECMETS_*.csv」にマッチするCSVファイルのみを取得
    csv_files = glob.glob(os.path.join(directory, "*10SECMETS_*.csv"))
    
    if not csv_files:
        print("該当するCSVファイルが見つかりませんでした。")
        return None

    # summaryファイルの抽出
    filename = os.path.basename(csv_files[0])
    index = filename.find("10SECMETS_")
    username = filename[:index]
    summaryfile = os.path.join(directory, username + ".csv")
    # print(username)
    try:
        summary_origin = pd.read_csv(summaryfile, encoding='utf-8', delimiter=',', header=1, usecols=range(26))  # ここでエンコーディングを指定
    except UnicodeDecodeError:
        # Now read the file using the correct delimiter, which is a comma.
        summary_origin = pd.read_csv(summaryfile, encoding='shift_jis', delimiter=',', header=1, usecols=range(26))
    summary_origin['日付'] = pd.to_datetime(summary_origin['日付']) # 日付をdatetime型に変換（必要な場合）
    
    for file in csv_files:
        # ファイル名から日付を抽出（'name_10SECMETS_YYYYMMDD.csv'形式を想定）
        filename = os.path.basename(file)
        date = filename.split('_')[-1].split('.')[0]
        
        # 10秒METs CSVファイルを読み込み（エンコーディング指定）
        try:
            df = pd.read_csv(file, encoding='utf-8', delimiter=',', header=2)  # ここでエンコーディングを指定
        except UnicodeDecodeError:
            # Now read the file using the correct delimiter, which is a comma.
            df = pd.read_csv(file, encoding='shift_jis', delimiter=',', header=2)
        
        # 必要な統計量を計算
        # エクササイズ
        ex_walk_activity = df[(df['運動種別'] == '歩行') & (df['活動強度'] >= 3.0)]['活動強度'].sum() / 360.0
        ex_life_activity = df[(df['運動種別'] == '生活活動') & (df['活動強度'] >= 3.0)]['活動強度'].sum() / 360.0
        ex_total_activity = ex_walk_activity + ex_life_activity
        # 時間(秒)
        time_walk = df[df['運動種別'] == '歩行'].shape[0] * 10
        time_life = df[df['運動種別'] == '生活活動'].shape[0] * 10
        time_sb = len(df.query('1.5 >= 活動強度 >= 1.0')) * 10
        time_lpa = len(df.query('3.0 > 活動強度 > 1.5')) * 10
        time_mpa = len(df.query('6.0 > 活動強度 >= 3.0')) * 10
        time_vpa = len(df.query('活動強度 >= 6.0')) * 10
        time_total = time_sb + time_lpa + time_mpa + time_vpa


        append_data = [date, ex_walk_activity, ex_life_activity, ex_total_activity, time_walk, time_life, time_sb, time_lpa, time_mpa, time_vpa, time_total]

        # ゼロ補正ありの場合
        if correction == "あり":
            correctrd_df = correction_from_1min_data(file)
            df = df.merge(correctrd_df[['時刻', 'synth_data']], on="時刻", how="left")
            df['活動強度'] = np.maximum(df['synth_data'], df['活動強度']) # '活動強度' を 'synth_data' と '活動強度' の大きい方に更新
            df.loc[(df['synth_data'] > 0) & (df['運動種別'] == '計測なし'), '運動種別'] = '生活活動' # 'synth_data' が 0 より大きくて'運動種別'が'計測なし'の場合に '運動種別' を '生活活動' に更新
            # 必要な統計量を計算
            # エクササイズ
            ex_walk_activity = df[(df['運動種別'] == '歩行') & (df['活動強度'] >= 3.0)]['活動強度'].sum() / 360.0
            ex_life_activity = df[(df['運動種別'] == '生活活動') & (df['活動強度'] >= 3.0)]['活動強度'].sum() / 360.0
            ex_total_activity = ex_walk_activity + ex_life_activity
            # 時間(秒)
            time_walk = df[df['運動種別'] == '歩行'].shape[0] * 10
            time_life = df[df['運動種別'] == '生活活動'].shape[0] * 10
            time_sb = len(df.query('1.5 >= 活動強度 >= 1.0')) * 10
            time_lpa = len(df.query('3.0 > 活動強度 > 1.5')) * 10
            time_mpa = len(df.query('6.0 > 活動強度 >= 3.0')) * 10
            time_vpa = len(df.query('活動強度 >= 6.0')) * 10
            time_total = time_sb + time_lpa + time_mpa + time_vpa

            append_data = append_data + [ex_walk_activity, ex_life_activity, ex_total_activity, time_walk, time_life, time_sb, time_lpa, time_mpa, time_vpa, time_total]

        # サマリデータに追加
        summary_data.append(append_data)

    
    # サマリデータをDataFrameに変換
    # ゼロ補正ありの場合
    if correction == "あり":
        summary_df = pd.DataFrame(summary_data, columns=['日付', '歩行Ex', '生活活動Ex', '合計Ex', '歩行時間(秒)', '生活活動時間(秒)', 'SB(秒)', 'LPA(秒)', 'MPA(秒)', 'VPA(秒)', '装着時間(秒)',
            '0補_歩行Ex', '0補_生活活動Ex', '0補_合計Ex', '0補_歩行時間(秒)', '0補_生活活動時間(秒)', '0補_SB(秒)', '0補_LPA(秒)', '0補_MPA(秒)', '0補_VPA(秒)', '0補_装着時間(秒)'])
    else:
        summary_df = pd.DataFrame(summary_data, columns=['日付', '歩行Ex', '生活活動Ex', '合計Ex', '歩行時間(秒)', '生活活動時間(秒)', 'SB(秒)', 'LPA(秒)', 'MPA(秒)', 'VPA(秒)', '装着時間(秒)'])

    summary_df['日付'] = pd.to_datetime(summary_df['日付']) # 日付をdatetime型に変換（必要な場合）
    summary_df = summary_df.sort_values(by='日付') # 日付で昇順に並び替え
    # weekday_map = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'} # 曜日を新しい列として追加(英語の場合この行もコメントアウト)
    # summary_df['曜日'] = summary_df['日付'].dt.weekday.map(weekday_map) # 曜日を新しい列として追加(日本語)
    # # summary_df['曜日'] = summary_df['日付'].dt.day_name() # 曜日を新しい列として追加(英語)
    # summary_df = summary_df[['日付', '曜日', '歩行Ex', '生活活動Ex', '合計Ex', '歩行時間(秒)', '生活活動時間(秒)', 'SB(秒)', 'LPA(秒)', 'MPA(秒)', 'VPA(秒)', '装着時間(秒)']] # 列の順序を変更（曜日を2列目に移動）
    summary_df.reset_index(drop=True, inplace=True) # インデックスをリセット


    summary_df = pd.merge(summary_origin, summary_df, on='日付', how='left')



    
    return summary_df

if __name__ == "__main__":
    # コマンドライン引数の取得
    if len(sys.argv) != 2:
        print("使い方: python csv_summary.py <ディレクトリパス>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    # ディレクトリが存在するか確認
    if not os.path.isdir(directory):
        print(f"エラー: 指定されたディレクトリが存在しません: {directory}")
        sys.exit(1)
    
    # CSVファイルを処理
    summary_df = process_csv_files(directory)
    
    if summary_df is not None:
        # サマリデータをCSVとして保存
        output_file = os.path.join(directory, "summary.csv")
        summary_df.to_csv(output_file, index=False, encoding='shift_jis')
        print(f"サマリファイルが保存されました: {output_file}")
    else:
        print("サマリファイルを生成できませんでした。")
