import sys
import pandas as pd


def make_all_summary(summary_df, window_size, threshold_min, threshold_days, dataid, birth, age, gender):
    """
    summary_df: 被験者ごとに作成されたデータフレーム
    window_size: スライドさせる期間
    threshold_min: 抽出する日の装着時間の下限値(36000 = 600分)
    ここで、0補正がONの場合はその0補正後の時間を採用する
    threshold_days: 抽出する日数の下限値 (4日)
    以降の引数はそのまま新規列として追加
    """
    # スライディングウィンドウの処理
    max_days = -1
    max_sum = -1
    best_window_indices = None

    # 日数優先　日数が同じの場合は合計装着時間で選択(合計装着時間も同じの場合は日付が古い期間を選択)
    for i in range(len(summary_df) - window_size + 1):
        window = summary_df.iloc[i:i + window_size]
        count_above_threshold = (window.iloc[:,-1] >= threshold_min).sum()
        total_wear_time = window.iloc[:,-1].sum()

        if count_above_threshold > max_days:
            max_days = count_above_threshold
            max_sum = total_wear_time
            best_window_indices = window.index
        elif count_above_threshold == max_days and total_wear_time > max_sum:
            max_sum = total_wear_time
            best_window_indices = window.index

    # 最適なウィンドウを selected_df として抽出
    # もし1日も閾値以上の日がない場合は最後の7日間を抽出
    selected_df = summary_df.loc[best_window_indices].reset_index(drop=True)

    # 現状 連続した7日間が取得されているので、ここから必要な情報のみ抜き出す
    selected_df = selected_df[selected_df.iloc[:,-1] >= threshold_min] # threshold_min 秒以上の日のみを残す
    if (selected_df.iloc[:,-1] >= threshold_min).sum() >= threshold_days:
        summary_df['サマリー利用'] = summary_df['日付'].isin(selected_df['日付']).astype(int)
    row_avg = selected_df.iloc[:, 4:].mean(axis=0).to_frame().T

    # print(summary_df)
    # print(selected_df)
    # print(row_avg)


    info_df = pd.DataFrame({
        'DATA-ID': [dataid],
        'BIRTH': [birth],
        'GENDER': [gender],
        'Hight(cm)': [summary_df['身長(cm)'].iloc[0]],
        'Weight(kg)': [summary_df['体重(kg)'].iloc[0]],
        'データ取得日': [pd.to_datetime(summary_df['日付']).min()], # 選択した日付ではなくデータの取得し始めた日
        'Age': [age],
        'BMI': [0.],
        '600分以上の日数': [(selected_df.iloc[:,-1] >= threshold_min).sum()],
        '': [pd.NA]
    })
    hight = float(info_df['Hight(cm)'].iloc[0])
    weight = float(info_df['Weight(kg)'].iloc[0])
    info_df.loc[info_df.index[0], 'BMI'] = 10000 * weight / (hight * hight)
    row_avg = row_avg.drop(columns=['身長(cm)', '体重(kg)'])
    return_df = pd.concat([info_df, row_avg], axis=1)

    # print(return_df)


    return return_df

if __name__ == "__main__":
    # コマンドライン引数の取得
    if len(sys.argv) != 2:
        print("使い方: python make_all_summary.py <ディレクトリパス>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # CSVファイルを読み込み
    try:
        df = pd.read_csv(filename, encoding='utf-8') 
    except UnicodeDecodeError:
        df = pd.read_csv(filename, encoding='shift_jis') 

    make_all_summary(df, 7, 36000, 4, "data001", "2000/4/1", 30, "F")

    # print(df)
