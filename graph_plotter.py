# graph_plotter.py

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image, ImageDraw, ImageFont
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd
import numpy as np


def create_plots_on_image(name, age, summary_df, image_path, output_dir, output_file, positions, text_position, font_path):
    """
    サマリデータを基に、4つのグラフを作成し、背景画像に指定された位置に配置します。
    最終的にPDFとして保存します。

    Args:
        name: 被験者氏名
        age: 被験者の年齢
        summary_df: データフレーム
        image_path: 画像フォルダのパス
        output_file: 出力PDFファイルのパス
        positions: 各グラフの左上と右下の座標のリスト [(x1, y1, x2, y2), ...]
        text_positions: テキスト(左端)の左上座標リスト(名前,　日付) [(x, y), ...]
    """


    # 旧バージョン 最大の装着時間が発生した7日間を抽出
    # summary_df['7日間の装着時間合計'] = summary_df['装着時間(秒)'].rolling(window=7).sum() # 7日間の「装着時間(秒)」の合計を計算 (rolling: 連続する期間)
    # max_index = summary_df['7日間の装着時間合計'].idxmax() # 最大の装着時間合計を持つインデックスを取得
    # summary_df = summary_df.loc[max_index - 6:max_index]

    # 新バージョン
    # 抽出方針
    # 1. 400分(24000秒)未満の日付を除外する
    # 2. 400分(24000秒)以上で連続した7日間があるか調べる
    # 3-1. [2.で連続した7日間がある場合] 最も装着時間の長い連続した7日間を抜粋
    # 3-2. [2.で連続した7日間がない場合] 最も装着時間の長い順に7日間を抜粋
    # 4. 400分(24000秒)以上600分(36000秒)未満のデータに対して、600分換算に変更
    # 5. [4.で7日間に満たない場合] 残りの日数をすべて平均値として7日間とする
    summary_df = extract_seven_days(summary_df, 24000, 36000)

    # 400分以上の日が1日もない場合
    if summary_df['装着時間(秒)'].isna().all():
        # 背景画像を開く
        background_image_path = f'{image_path}/background_error.png' # 両方達成
        background_image = Image.open(background_image_path)

        # テキストを貼り付ける
        draw = ImageDraw.Draw(background_image)
        font_size = 65
        font = ImageFont.truetype(font_path, font_size)
        # draw.text([825,905], name, fill="black", font=font, align="left") # 左寄せ
        # draw.text([1075,945], name, fill="black", font=font, anchor='mm') # 中央寄せ
        draw.text([540,1080], name, fill="black", font=font, anchor='mm') # 中央寄せ

        # 結果をPDFで保存
        background_image.save(f'{output_dir}/{output_file}.pdf', "PDF")
        return





    days_jp = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
    date = summary_df['日付'].apply(lambda d: d.strftime('%m/%d') + ' (' + days_jp[d.weekday()] + ')' if d.year >= 2000 else '推測値')
    date.reset_index(drop=True, inplace=True)  # インデックスの振り直し
    Sat=date.index[date.str.contains('土')].tolist()
    Sun=date.index[date.str.contains('日')].tolist()
    Mean=date.index[date.str.contains('推測値')].tolist()
    if "換算" in summary_df.columns:
        Conv=summary_df[summary_df["換算"] == 1].index.tolist()
        date[Conv] = date[Conv] + "*"
    else:
        Conv = []




    padding = ""
    for i in range(len(date)):
        if date[i] == '推測値':
            date[i] = f'{padding}推測値'
            padding = padding + " "


    # name = f"{name}({age})"
    text_date = pd.to_datetime(summary_df['日付'], format='%Y/%m/%d').dt.strftime('%m/%d')
    # text_data = [(name, text_position[0], 100), (text_date.iloc[0] + '〜' + text_date.iloc[-1], text_position[1], 50)]
    text_data = [(name, text_position[0], 100)]

    if age < 65:
        recommendation_text = "18〜64歳"
        recommendation_mets = 23.0
        recommendation_walk = 8000.0
    else:
        recommendation_text = "65歳以上"
        recommendation_mets = 15.0
        recommendation_walk = 6000.0

    # 達成度の計算
    # mets
    percent_mets = summary_df['合計Ex'].sum() / recommendation_mets * 100
    if percent_mets >= 100:
        achievement_mets = 3
    elif 75 <= percent_mets < 100:
        achievement_mets = 2
    elif 50 <= percent_mets < 75:
        achievement_mets = 1
    else:
        achievement_mets = 0
    # 歩数
    percent_walk = summary_df['歩数合計(歩)'].mean() / recommendation_walk * 100
    if percent_walk >= 100:
        achievement_walk = 3
    elif 75 <= percent_walk < 100:
        achievement_walk = 2
    elif 50 <= percent_walk < 75:
        achievement_walk = 1
    else:
        achievement_walk = 0


    # 各グラフを個別に画像として保存
    graph_images = []

    #文字の大きさ
    fontsize_default = 20
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)

    for i in range(4):
        # グラフを作成
        plt.rcParams['font.size'] = fontsize_default
        plt.rcParams['font.family'] = font_prop.get_name()
        fig, ax = plt.subplots(facecolor='none')
        ax.set_facecolor('none')

        # それぞれのグラフの描画
        if i == 0:
            categories = ["あなたの\n1週間の活動量", f"{recommendation_text}の推奨値\n(厚生労働省)"]
            values = [summary_df['合計Ex'].sum(), recommendation_mets]
            # 基準値（推奨値）
            base_value = recommendation_mets
            ax.axhline(y=100, color='black', linestyle='--', zorder=1)
            # y軸の値をパーセンテージに変換
            values = [value / base_value * 100 for value in values]
            bars = ax.bar(categories, values, color='lightpink')
            bars[1].set_color('lightgray')
            # 棒グラフの中に数値と単位を表示
            y_max = ax.get_ylim()[1]
            for j, bar in enumerate(bars):
                height = bar.get_height()
                if height < y_max * 0.15:
                    text_height = height + y_max * 0.1
                else:
                    text_height = height / 2
                ax.text(
                    bar.get_x() + bar.get_width() / 2,  # 棒の中央に配置
                    text_height,  # 棒の高さの中間に配置
                    f'{values[j] * base_value / 100:.1f} \n[メッツ・時]',  # 数値に単位を追加
                    ha='center',  # 水平方向で中央揃え
                    va='center',  # 垂直方向で中央揃え
                    color='black',  # 文字色
                    fontsize=20  # フォントサイズ
                )
            if values[0] < values[1] * 2:
                plt.yticks(np.arange(0, 101, 25))
            elif values[1] * 2 < values[0] < values[1] * 4:
                plt.yticks(np.arange(0, 101, 50)) 
            else:
                plt.yticks(np.arange(0, 101, 100)) 
        elif i == 1:
            bars_walk = ax.bar(date, summary_df['歩行Ex'],
                tick_label=date, align="center",
                color="cornflowerblue")
            bars_life = ax.bar(date, summary_df['生活活動Ex'],
                tick_label=date, align="center",
                color="darkorange", bottom=summary_df['歩行Ex'])
            # 棒グラフの中に数値と単位を表示
            for bar in bars_walk:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,  # 棒の中央に配置
                    height / 2,  # 棒の高さの中間に配置
                    f'{height:.1f}',  # 数値に単位を追加
                    ha='center',  # 水平方向で中央揃え
                    va='center',  # 垂直方向で中央揃え
                    color='black',  # 文字色
                    fontsize=20  # フォントサイズ
                )
            y_max = ax.get_ylim()[1]
            for  bar, bar2 in zip(bars_life, bars_walk):
                height = bar.get_height()
                if height < y_max * 0.1:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,  # 棒の中央に配置
                        height + bar2.get_height() + y_max * 0.1,  # 棒の上部に配置
                        f'{height:.1f}',  # 数値に単位を追加
                        ha='center',  # 水平方向で中央揃え
                        va='center',  # 垂直方向で中央揃え
                        color='black',  # 文字色
                        fontsize=20  # フォントサイズ
                    )
                else:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,  # 棒の中央に配置
                        height / 2 + bar2.get_height(),  # 棒の高さの中間に配置
                        f'{height:.1f}',  # 数値に単位を追加
                        ha='center',  # 水平方向で中央揃え
                        va='center',  # 垂直方向で中央揃え
                        color='black',  # 文字色
                        fontsize=20  # フォントサイズ
                    )
            plt.xticks(np.arange(len(date))-0.2, labels=date, rotation=70)
            for sat in Sat:
                plt.gca().get_xticklabels()[sat].set_color('mediumblue')
            for sun in Sun:
                plt.gca().get_xticklabels()[sun].set_color('crimson')
            for mean_x in Mean:
                bars_life[mean_x].set_color('gray')
                bars_walk[mean_x].set_color('lightgray')
                # plt.gca().get_xticklabels()[mean_x].set_color('gray')
                # plt.gca().get_xticklabels()[mean_x].set_fontsize(12)
                # plt.gca().get_xticklabels()[mean_x].set_position((plt.gca().get_xticklabels()[mean_x].get_position()[0] + 2, plt.gca().get_xticklabels()[mean_x].get_position()[1]))
                # plt.gca().get_xticklabels()[mean_x].set_ha('right')
            for conv in Conv:
                bars_life[conv].set_color('gray')
                bars_walk[conv].set_color('lightgray')
                # plt.gca().get_xticklabels()[conv].set_color('green')
            ax.set_xticklabels([t.get_text() for t in ax.get_xticklabels()])
        elif i == 2:
            categories = ["あなたの\n歩数(1日平均)", f"{recommendation_text}の推奨値\n(厚生労働省)"]
            values = [summary_df['歩数合計(歩)'].mean(), recommendation_walk]
            # 基準値（推奨値）
            base_value = recommendation_walk
            ax.axhline(y=100, color='black', linestyle='--', zorder=1)
            # y軸の値をパーセンテージに変換
            values = [value / base_value * 100 for value in values]
            bars = ax.bar(categories, values, color='lightpink')
            # bars = ax.bar(categories, values, color='lightpink')
            bars[1].set_color('lightgray')
            # 棒グラフの中に数値と単位を表示
            y_max = ax.get_ylim()[1]
            for j, bar in enumerate(bars):
                height = bar.get_height()
                if height < y_max * 0.1:
                    text_height = height + y_max * 0.1
                else:
                    text_height = height / 2
                ax.text(
                    bar.get_x() + bar.get_width() / 2,  # 棒の中央に配置
                    text_height,  # 棒の高さの中間に配置
                    f'{int(values[j] * base_value / 100)} 歩',  # 数値に単位を追加
                    ha='center',  # 水平方向で中央揃え
                    va='center',  # 垂直方向で中央揃え
                    color='black',  # 文字色
                    fontsize=20  # フォントサイズ
                )
            plt.yticks(np.arange(0, 101, 25))
        elif i == 3:
            bars_mpa = ax.bar(date, summary_df['MPA(秒)']/60,
                tick_label=date, align="center",
                color="#ff99cc")
            bars_vpa = ax.bar(date, summary_df['VPA(秒)']/60,
                tick_label=date, align="center",
                color="red", bottom=summary_df['MPA(秒)']/60)
            ax.axhline(y=22, color='black', linestyle='--')
            plt.xticks(np.arange(len(date))-0.2, labels=date, rotation=70)
            for sat in Sat:
                plt.gca().get_xticklabels()[sat].set_color('mediumblue')
            for sun in Sun:
                plt.gca().get_xticklabels()[sun].set_color('crimson')
            for mean_x in Mean:
                bars_vpa[mean_x].set_color('gray')
                bars_mpa[mean_x].set_color('lightgray')
                # plt.gca().get_xticklabels()[mean_x].set_color('gray')
                # plt.gca().get_xticklabels()[mean_x].set_fontsize(12)
                # plt.gca().get_xticklabels()[mean_x].set_ha('right')
                # plt.gca().get_xticklabels()[mean_x].set_position((plt.gca().get_xticklabels()[mean_x].get_position()[0] + 0.5, plt.gca().get_xticklabels()[mean_x].get_position()[1]))
            for conv in Conv:
                bars_vpa[conv].set_color('gray')
                bars_mpa[conv].set_color('lightgray')
                # plt.gca().get_xticklabels()[conv].set_color('green')
        else:
            pass

        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['top'].set_visible(False)
        plt.tight_layout()

        # グラフを画像に変換
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        graph_images.append(Image.open(buf).convert("RGBA"))

        # メモリ解放
        plt.close(fig)


    # for i, (graph_image, pos) in enumerate(zip(graph_images, positions)):
    #     # グラフ画像のサイズを指定された位置に合わせてリサイズ
    #     graph_image_resized = graph_image.resize((pos[2] - pos[0], pos[3] - pos[1]))

    #     # PNGファイルとして保存
    #     graph_image_resized.save(f"graph_{i}.png", "PNG")

    # 背景画像を開く
    if percent_mets >= 100:
        if percent_walk >= 100:
            background_image_path = f'{image_path}/background_1.png' # 両方達成
        else:
            background_image_path = f'{image_path}/background_2.png' # 身体活動量のみ達成
    else:
        if percent_walk >= 100:
            background_image_path = f'{image_path}/background_4.png' # 歩数のみ達成
        else:
            background_image_path = f'{image_path}/background_3.png' # 両方達成せず
    background_image = Image.open(background_image_path)

    # グラフ画像を背景画像に貼り付ける
    for i, (graph_image, pos) in enumerate(zip(graph_images, positions)):
        # グラフ画像のサイズを指定された位置に合わせてリサイズ
        graph_image_resized = graph_image.resize((pos[2] - pos[0], pos[3] - pos[1]))
        # 背景画像に貼り付ける（マスクで透明部分を除外）
        background_image.paste(graph_image_resized, box=pos, mask=graph_image_resized)


    # 達成度の星を貼り付ける
    # 星画像のサイズをリサイズ

    # star_image = Image.open(f'{image_path}/star.png')
    # star_positions = [(1867, 990), (443, 2291)]
    # star_size = 132
    # star_image_resized = star_image.resize((star_size, star_size))
    # for i in range(achievement_mets):
    #     # 背景画像に貼り付ける（マスクで透明部分を除外）
    #     background_image.paste(star_image_resized, box=[star_positions[0][0] + int(i * star_size * 1.2), star_positions[0][1]], mask=star_image_resized)
    # for i in range(achievement_walk):
    #     # 背景画像に貼り付ける（マスクで透明部分を除外）
    #     background_image.paste(star_image_resized, box=[star_positions[1][0] + int(i * star_size * 1.2), star_positions[1][1]], mask=star_image_resized)
    
    # テキストを貼り付ける
    draw = ImageDraw.Draw(background_image)
    for text, position, size in text_data:
        # フォントの設定 (フォントパスとサイズを指定)
        font_size = size  # フォントサイズ
        font = ImageFont.truetype(font_path, font_size)
        # フォントなしのデフォルト設定でテキストを追加
        # draw.text(position, text, fill="black", font=font, align="left")
        draw.text(position, text, fill="black", font=font, anchor='mm')

    # 換算値に関するテキストを貼り付ける
    if "換算" in summary_df.columns:
        font_size = 30  # フォントサイズ
        font = ImageFont.truetype(font_path, font_size)
        # フォントなしのデフォルト設定でテキストを追加
        # draw.text([2950,600], '*補正値です。\n「解析結果シートのみかた」もご覧ください。', fill="black", font=font, align="left")
        # draw.text([3050,1950], '*補正値です。\n「解析結果シートのみかた」もご覧ください。', fill="black", font=font, align="left")
        draw.text([2950,600+770], '*補正値です。\n「解析結果シートのみかた」もご覧ください。', fill="black", font=font, align="left")
        draw.text([3050,1950+770], '*補正値です。\n「解析結果シートのみかた」もご覧ください。', fill="black", font=font, align="left")


    # 結果をPDFで保存
    background_image.save(f'{output_dir}/{output_file}.pdf', "PDF", dpi=(350, 350))



# 条件に基づいて7日間を抽出
def extract_seven_days(summary_df, th1, th2):
    # 1. 400分(24000秒)未満の日付を除外したデータと600分(24000秒)未満の日付を除外したデータを作成
    filtered_df_th1 = summary_df[summary_df['装着時間(秒)'] >= th1].reset_index(drop=True)
    filtered_df_th2 = summary_df[summary_df['装着時間(秒)'] >= th2].reset_index(drop=True)
    
    # 2.1 400分(24000秒)以上で連続した7日間の合計装着時間が最も長い期間を探す
    max_sum = 0
    best_7_days = pd.DataFrame()
    for i in range(len(filtered_df_th2) - 6):  # 連続した7日間を取り出せる範囲までループ
        week_df = filtered_df_th2.iloc[i:i + 7]  # 連続する7日間をスライス
        if (week_df['日付'].diff().dropna() == pd.Timedelta(days=1)).all():  # 7日間が連続しているか確認
            week_sum = week_df['装着時間(秒)'].sum()
            if week_sum > max_sum:  # 合計装着時間が最大の7日間を記録
                max_sum = week_sum
                best_7_days = week_df

    # 2.2 2.1で見つからなかった場合は400分(24000秒)以上で連続した7日間の合計装着時間が最も長い期間を探す
    if best_7_days.empty:
        max_sum = 0
        best_7_days = pd.DataFrame()
        for i in range(len(filtered_df_th1) - 6):  # 連続した7日間を取り出せる範囲までループ
            week_df = filtered_df_th1.iloc[i:i + 7]  # 連続する7日間をスライス
            if (week_df['日付'].diff().dropna() == pd.Timedelta(days=1)).all():  # 7日間が連続しているか確認
                week_sum = week_df['装着時間(秒)'].sum()
                if week_sum > max_sum:  # 合計装着時間が最大の7日間を記録
                    max_sum = week_sum
                    best_7_days = week_df

    # 3. 7日間の抜粋
    if best_7_days.empty:
        # 3-2. 最も装着時間の長い順に7日間を抜粋(400分以上も含む)
        top_7_days = filtered_df_th1.nlargest(7, '装着時間(秒)')
    else:
        # 3-1. 装着時間が閾値を超えたのが連続した7日間で、その中でも合計時間が最も長い7日間を抜粋
        top_7_days = best_7_days

    # 日付でソートして戻す
    top_7_days = top_7_days.sort_values('日付').reset_index(drop=True)


    # 4. 第一閾値以上、第二閾値以下の装着時間の場合、
    for index, row in top_7_days.iterrows():
        if th1 <= row['装着時間(秒)'] < th2:
            # 条件に合致する場合の値変更
            ratio = float(th2/row['装着時間(秒)'])
            top_7_days.at[index, '装着時間(秒)'] = int(top_7_days.at[index, '装着時間(秒)'] * ratio)
            top_7_days.at[index, '歩数合計(歩)'] = int(top_7_days.at[index, '歩数合計(歩)'] * ratio)
            top_7_days.at[index, '歩行Ex'] = top_7_days.at[index, '歩行Ex'] * ratio
            top_7_days.at[index, '生活活動Ex'] = top_7_days.at[index, '生活活動Ex'] * ratio
            top_7_days.at[index, '合計Ex'] = top_7_days.at[index, '合計Ex'] * ratio
            top_7_days.at[index, 'MPA(秒)'] = int(top_7_days.at[index, 'MPA(秒)'] * ratio)
            top_7_days.at[index, 'VPA(秒)'] = int(top_7_days.at[index, 'VPA(秒)'] * ratio)
            top_7_days.at[index, '換算'] = 1
            # print(row)
            # print(ratio)
            # print(top_7_days.iloc[index])

        
    # 5. 7日間に満たない場合、残りの日数をすべて平均値として7日間とする
    if 1 <= len(top_7_days) < 7:
        mean_row = pd.DataFrame({
            # '日付': [f'平均値({top_7_days["日付"].min().strftime("%Y-%m-%d")}-{top_7_days["日付"].max().strftime("%Y-%m-%d")})'],
            '日付':  [pd.Timestamp('1990-01-01')],
            '装着時間(秒)': [int(top_7_days['装着時間(秒)'].mean())],
            '歩数合計(歩)': [int(top_7_days['歩数合計(歩)'].mean())],
            '歩行Ex': [top_7_days['歩行Ex'].mean()],
            '生活活動Ex': [top_7_days['生活活動Ex'].mean()],
            '合計Ex': [top_7_days['合計Ex'].mean()],
            'MPA(秒)': [int(top_7_days['MPA(秒)'].mean())],
            'VPA(秒)': [int(top_7_days['VPA(秒)'].mean())],
        })
        # 残りの日数分を平均値行で埋める
        while len(top_7_days) < 7:
            top_7_days = pd.concat([top_7_days, mean_row], ignore_index=True)
            mean_row['日付'] = mean_row['日付'] + pd.Timedelta(days=7)
        

    # print(top_7_days)
        
    return top_7_days




