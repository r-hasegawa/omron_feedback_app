import sys
import pandas as pd


def make_all_summary_consecutive(summary_df, correction, consecutive_min, consecutive_max, threshold_min, dataid, birth, age, gender):
    """
    summary_df: 被験者ごとに作成されたデータフレーム
    correction: 0補正があるかどうか
    consecutive_min: 連続日数の下限値
    consecutive_max: 連続日数の上限値
    threshold_min: 抽出する日の装着時間の下限値(36000 = 600分)
    ここで、0補正がONの場合はその0補正後の時間を採用する
    以降の引数はそのまま新規列として追加
    """

    if correction == "あり":
        wear_time_col_name = '0補_装着時間(秒)'
    else:
        wear_time_col_name = '装着時間(秒)'

    # 日付をdatetimeに変換（必要な場合）
    summary_df['日付'] = pd.to_datetime(summary_df['日付'])

    filtered_df = summary_df[summary_df[wear_time_col_name] >= threshold_min].sort_values('日付').reset_index(drop=True)
    if 'サマリー利用' in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=['サマリー利用'])

    # 日付の差分（1日単位）で連続期間をグループ化
    filtered_df['diff'] = filtered_df['日付'].diff().dt.days
    filtered_df['group'] = (filtered_df['diff'] != 1).cumsum()

    # 条件を満たすグループを抽出
    candidates = []
    for _, group_df in filtered_df.groupby('group'):
        n = len(group_df)
        if n < consecutive_min:
            continue

        # スライドウィンドウで consecutive_max 以下の連続期間をすべて候補に
        for i in range(n - consecutive_min + 1):
            for j in range(consecutive_min, min(consecutive_max, n - i) + 1):
                sub_df = group_df.iloc[i:i + j]
                total_time = sub_df['装着時間(秒)'].sum()
                candidates.append({
                    'length': j,
                    'total_time': total_time,
                    'data': sub_df
                })

    # 候補がなければ空のDataFrameを返す
    if not candidates:
        return pd.DataFrame()

    # 最も長い期間を優先、同じ長さなら合計装着時間が多いもの
    candidates.sort(key=lambda x: (-x['length'], -x['total_time']))
    selected_df = candidates[0]['data']

    selected_df.reset_index(drop=True)
    selected_df = selected_df.drop(columns=['diff', 'group'])




    # 現状 thresholdを超えた日の連続したX日間が取得されている
    summary_df['サマリー利用_連続'] = summary_df['日付'].isin(selected_df['日付']).astype(int)
    row_avg = selected_df.iloc[:, 4:].mean(axis=0).to_frame().T

    # print(selected_df)
    # print(summary_df)


    info_df = pd.DataFrame({
        'DATA-ID': [dataid],
        'BIRTH': [birth],
        'GENDER': [gender],
        'Hight(cm)': [summary_df['身長(cm)'].iloc[0]],
        'Weight(kg)': [summary_df['体重(kg)'].iloc[0]],
        'データ取得日': [pd.to_datetime(summary_df['日付']).min()], # 選択した日付ではなくデータの取得し始めた日
        'Age': [age],
        'BMI': [0.],
        '連続日数': [(selected_df[wear_time_col_name] >= threshold_min).sum()],
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

    ret = make_all_summary_consecutive(df, "あり", 4, 7, 30000, "data001", "2000/4/1", 30, "F")
