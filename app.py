# app.py

import tkinter as tk
from tkinter import filedialog, messagebox
from csv_summary import process_csv_files
from make_all_summary import make_all_summary
from graph_plotter import create_plots_on_image
import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

def on_closing():
    root.quit()
    root.destroy()
    sys.exit()  # 明示的にPythonプロセスを終了


class CSVProcessorApp:
    def __init__(self, root):
        """
        GUIアプリケーションの初期設定を行います。
        """
        self.root = root
        self.root.title("CSV処理アプリケーション")

        # ウィンドウサイズの設定 (幅x高さ)
        window_width = 600
        window_height = 450
        
        # 画面中央に配置するための計算
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        position_x = (screen_width // 2) - (window_width // 2)
        position_y = (screen_height // 2) - (window_height // 2)
        
        # ウィンドウサイズと位置を設定
        self.root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        #-----------------------------------メインページ-----------------------------
        # メインページフレーム作成
        self.main_frame = tk.Frame()
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(anchor="center", expand=1, pady=10)
        self.changePageButton_sp = tk.Button(button_frame, text="1つのフォルダを処理", command=lambda : self.changePage(self.single_process_frame, "single"))
        self.changePageButton_sp.pack(side=tk.LEFT, padx=10)
        self.changePageButton_mp = tk.Button(button_frame, text="複数フォルダを処理", command=lambda : self.changePage(self.multiple_process_frame, "multiple"))
        self.changePageButton_mp.pack(side=tk.LEFT, padx=10)

        #-----------------------------------単数フォルダ処理用-----------------------------
        # 単数フォルダ処理用フレーム作成
        self.single_process_frame = tk.Frame()
        self.single_process_frame.grid(row=0, column=0, sticky="nsew")

        # 戻るボタン
        self.backButton_sp = tk.Button(self.single_process_frame, text="モード選択に戻る", command=lambda : self.changePage(self.main_frame, "main"))
        self.backButton_sp.pack(anchor="ne")

        # ラベルとボタンの作成
        self.label_sp = tk.Label(self.single_process_frame, text="CSVファイルのあるディレクトリを選択:")
        self.label_sp.pack(pady=10)
        self.select_button_sp = tk.Button(self.single_process_frame, text="ディレクトリ選択", command=self.browse_directory)
        self.select_button_sp.pack(pady=5)
        self.directory_label_sp = tk.Label(self.single_process_frame, text="選択されたディレクトリ: なし", wraplength=500)
        self.directory_label_sp.pack(pady=5)

        # 名前と年齢のエントリーフィールド
        name_frame = tk.Frame(self.single_process_frame)
        name_frame.pack(pady=10)
        self.name_label = tk.Label(name_frame, text="名前:")
        self.name_label.pack(side=tk.LEFT, padx=5)
        self.name_entry = tk.Entry(name_frame)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        self.age_label = tk.Label(name_frame, text="年齢:")
        self.age_label.pack(side=tk.LEFT, padx=5)
        self.age_entry = tk.Entry(name_frame)
        self.age_entry.pack(side=tk.LEFT, padx=5)

        # 0補正の選択
        zero_interpolation_frame_sp = tk.Frame(self.single_process_frame)
        zero_interpolation_frame_sp.pack(pady=10)
        self.correction_label_sp = tk.Label(zero_interpolation_frame_sp, text="0補正しますか:")
        self.correction_label_sp.pack(side="left", padx=5)
        self.correction_var_sp = tk.StringVar(value="あり")  # デフォルトの選択肢を「なし」に設定
        # ラジオボタンを横並びにするためのフレーム
        radio_frame_sp = tk.Frame(zero_interpolation_frame_sp)
        radio_frame_sp.pack(pady=5)
        # ラジオボタン「あり」
        self.correction_yes_sp = tk.Radiobutton(radio_frame_sp, text="あり", variable=self.correction_var_sp, value="あり")
        self.correction_yes_sp.pack(side="left")
        # ラジオボタン「なし」
        self.correction_no_sp = tk.Radiobutton(radio_frame_sp, text="なし", variable=self.correction_var_sp, value="なし")
        self.correction_no_sp.pack(side="left")
        
        self.process_button = tk.Button(self.single_process_frame, text="CSVファイルを処理", command=self.process_csv_files)
        self.process_button.pack(pady=20)

        #-----------------------------------複数フォルダ処理用-----------------------------
        # 複数フォルダ処理用フレーム作成
        self.multiple_process_frame = tk.Frame()
        self.multiple_process_frame.grid(row=0, column=0, sticky="nsew")
        
        # 戻るボタン
        self.backButton_mp = tk.Button(self.multiple_process_frame, text="モード選択に戻る", command=lambda : self.changePage(self.main_frame, "main"))
        self.backButton_mp.pack(anchor="ne")

        # ラベルとボタンの作成
        self.label_mp = tk.Label(self.multiple_process_frame, text="CSVファイルのあるディレクトリを選択:")
        self.label_mp.pack(pady=10)
        self.select_button_mp = tk.Button(self.multiple_process_frame, text="ディレクトリ選択", command=self.browse_directory)
        self.select_button_mp.pack(pady=5)
        self.directory_label_mp = tk.Label(self.multiple_process_frame, text="選択されたディレクトリ: なし", wraplength=500)
        self.directory_label_mp.pack(pady=5)

        self.select_info_button = tk.Button(self.multiple_process_frame, text="情報シート選択", command=self.browse_sheet)
        self.select_info_button.pack(pady=5)
        self.sheet_label = tk.Label(self.multiple_process_frame, text="選択されたシート: なし", wraplength=300)
        self.sheet_label.pack(pady=5)

        # # 名前と年齢のエントリーフィールド
        # name_frame = tk.Frame(self.multiple_process_frame)
        # name_frame.pack(pady=10)
        # self.name_label = tk.Label(name_frame, text="名前:")
        # self.name_label.pack(side=tk.LEFT, padx=5)
        # self.name_entry = tk.Entry(name_frame)
        # self.name_entry.pack(side=tk.LEFT, padx=5)
        # self.age_label = tk.Label(name_frame, text="年齢:")
        # self.age_label.pack(side=tk.LEFT, padx=5)
        # self.age_entry = tk.Entry(name_frame)
        # self.age_entry.pack(side=tk.LEFT, padx=5)

        # 0補正の選択
        zero_interpolation_frame_mp = tk.Frame(self.multiple_process_frame)
        zero_interpolation_frame_mp.pack(pady=10)
        self.correction_label_mp = tk.Label(zero_interpolation_frame_mp, text="0補正しますか:")
        self.correction_label_mp.pack(side="left", padx=5)
        self.correction_var_mp = tk.StringVar(value="あり")  # デフォルトの選択肢を「なし」に設定
        # ラジオボタンを横並びにするためのフレーム
        radio_frame_mp = tk.Frame(zero_interpolation_frame_mp)
        radio_frame_mp.pack(pady=5)
        # ラジオボタン「あり」
        self.correction_yes_mp = tk.Radiobutton(radio_frame_mp, text="あり", variable=self.correction_var_mp, value="あり")
        self.correction_yes_mp.pack(side="left")
        # ラジオボタン「なし」
        self.correction_no_mp = tk.Radiobutton(radio_frame_mp, text="なし", variable=self.correction_var_mp, value="なし")
        self.correction_no_mp.pack(side="left")

        # 新しいボタン: CSVファイル群を処理
        self.process_multiple_button = tk.Button(self.multiple_process_frame, text="CSVファイル群を処理", command=self.process_multiple_csv_files)
        self.process_multiple_button.pack(pady=10)

        # 状態ラベル
        self.tx = tk.StringVar()
        self.tx.set("操作待機中...")
        self.status_label = tk.Label(self.multiple_process_frame, textvariable=self.tx)
        self.status_label.pack(anchor="se", padx=5)

        #--------------------------------------------------------------------------

        #main_frameを一番上に表示
        self.main_frame.tkraise()
        self.current_mode = "main"

    def changePage(self, page, mode):
        '''
        画面遷移用の関数
        '''
        page.tkraise()
        self.current_mode = mode
    
    def browse_directory(self):
        """
        ディレクトリ選択ダイアログを開き、ユーザーが選択したディレクトリを保存します。
        デフォルトパスは現在の作業ディレクトリに設定されます。
        """
        initialdir = os.getcwd()  # 現在の作業ディレクトリを取得

        if getattr(sys, 'frozen', False):
          initialdir = os.path.dirname(os.path.abspath(sys.executable))
          print('EXE abs dirname: ', os.path.dirname(os.path.abspath(sys.executable)))
        else:
          initialdir = os.path.dirname(os.path.abspath(__file__))
          print('PYTHON abs dirname: ', os.path.dirname(os.path.abspath(__file__)))

        if self.current_mode == "single":
            self.directory_sp = filedialog.askdirectory(initialdir=initialdir)
            if self.directory_sp:
                self.directory_label_sp.config(text=f"選択されたディレクトリ: {self.directory_sp}")
        else:
            self.directory_mp = filedialog.askdirectory(initialdir=initialdir)
            if self.directory_mp:
                self.directory_label_mp.config(text=f"選択されたディレクトリ: {self.directory_mp}")


    def browse_sheet(self):
        """
        ディレクトリ選択ダイアログを開き、ユーザーが選択したディレクトリを保存します。
        デフォルトパスは現在の作業ディレクトリに設定されます。
        """
        initialdir = os.getcwd()  # 現在の作業ディレクトリを取得

        if getattr(sys, 'frozen', False):
          initialdir = os.path.dirname(os.path.abspath(sys.executable))
          print('EXE abs dirname: ', os.path.dirname(os.path.abspath(sys.executable)))
        else:
          initialdir = os.path.dirname(os.path.abspath(__file__))
          print('PYTHON abs dirname: ', os.path.dirname(os.path.abspath(__file__)))

        self.csv_sheet = filedialog.askopenfilename(
            initialdir=initialdir,
            title="ファイルを選択してください",
            filetypes=[("CSVファイル", "*.csv")]
            )
        if self.csv_sheet:
            self.sheet_label.config(text=f"選択されたシート: {self.csv_sheet}")

    def process_csv_files(self):
        if not hasattr(self, 'directory_sp'):
            messagebox.showwarning("エラー", "ディレクトリが選択されていません")
            return

        try:
            summary_df = process_csv_files(self.directory_sp, self.correction_var_sp.get())
            self.create_plots_and_save(summary_df, self.directory_sp, self.correction_var_sp.get())

            messagebox.showinfo("成功", "サマリCSVとPDFレポートが生成されました")
        except Exception as e:
            messagebox.showerror("エラー", f"{self.directory_sp} の処理中にエラーが発生しました: {e}")



    def process_multiple_csv_files(self):
        if not hasattr(self, 'directory_mp'):
            messagebox.showwarning("エラー", "ディレクトリが選択されていません")
            return

        if not hasattr(self, 'csv_sheet'):
            messagebox.showwarning("エラー", "被験者リストが選択されていません")
            return

        # 被験者情報の読み取り
        if not self.csv_sheet:
            print("該当する被験者リストが見つかりませんでした。")
            return

        print(self.csv_sheet)

        try:
            subject_df = pd.read_csv(self.csv_sheet, encoding='utf-8', delimiter=',', header=0, usecols=range(5))  # 2025/05/20 追記 GENDER列を読み込みに追加
        except UnicodeDecodeError:
            subject_df = pd.read_csv(self.csv_sheet, encoding='shift_jis', delimiter=',', header=0, usecols=range(5)) # 2025/05/20 追記 GENDER列を読み込みに追加
        # subject_df['生年月日'] = pd.to_datetime(subject_df['生年月日']) # 日付をdatetime型に変換（必要な場合）
        
        # サブディレクトリを走査して処理

        all_df_list = [] # 2025/05/20 追記 被験者全体用のリスト

        subdirectories = [d for d in os.listdir(self.directory_mp) if os.path.isdir(os.path.join(self.directory_mp, d))]
        total_count = len(subdirectories)
        processed_count = 0
        success_count = 0  # 成功した処理回数

        for subdirectory in os.listdir(self.directory_mp):    
            full_path = os.path.join(self.directory_mp, subdirectory)
            self.tx.set(f'処理中({processed_count}/{total_count}完了) - {subdirectory}')
            self.status_label.update()

            if os.path.isdir(full_path):
                processed_count += 1
                # "フォルダ名"列でsubdirectoryと一致する行を検索
                matching_rows = subject_df[subject_df["DATA-ID"] == subdirectory]
                if len(matching_rows) == 0:
                    messagebox.showerror("エラー", f"{subdirectory} は被験者リストには見つかりませんでした")
                elif len(matching_rows) == 1:
                    birth = matching_rows.iloc[0]["BIRTH"]
                    name = matching_rows.iloc[0]["NAME"]
                    if birth == "" or name == "":
                        messagebox.showerror("エラー", f"{subdirectory} に該当する被験者の氏名や生年月日が未入力です")
                        continue
                    try:
                        birth_date = datetime.strptime(birth, "%Y/%m/%d")
                    except Exception as e:
                        messagebox.showerror("エラー", f"{subdirectory} に該当する被験者の生年月日の型が異なります: {e}")
                        continue
                    try:
                        summary_df = process_csv_files(full_path, self.correction_var_mp.get())
                        min_date = pd.to_datetime(summary_df['日付']).min()
                        age = min_date.year - birth_date.year - ((min_date.month, min_date.day) < (birth_date.month, birth_date.day))
                        """
                        2025/05/20 追記
                        被験者全体のサマリーファイルを作成する to金本先生【GENDER】列を追加すること！！
                        summary_df の [歩行カロリー]列(4) から [0補_装着時間(秒)]列(35) or [0補_装着時間(秒)]列(45) までの列の平均を1行に
                        [身長(cm)]列(22) と [体重(kg)]列(23) を [Hight(cm)] および [Weigh(kg)] にリネームしたのち左側に寄せる
                        DATA-ID,BIRTH,GENDER,Hight(cm),Weight(kg),データ吸い出し日,Age,BMI,600分以上の日数,[summary_dfのデータの平均] という順番に並べる
                        """
                        row_all_df = make_all_summary(summary_df, 7, 36000, 4, matching_rows.iloc[0]["DATA-ID"], birth, age, matching_rows.iloc[0]["GENDER"])
                        # もし1日も閾値以上の日がない場合は最後の7日間を抽出するので、ここで判別 4日以上の場合CSVに記載
                        if row_all_df['600分以上の日数'].iloc[0] >= 4:
                            all_df_list.append(row_all_df)
                        """
                        2025/05/20 追記ここまで
                        """
                        self.create_plots_and_save(summary_df, full_path, self.correction_var_mp.get(), name, age)
                        success_count += 1
                    except Exception as e:
                        print(e)
                        import traceback
                        traceback.print_exc()
                        messagebox.showerror("エラー", f"{subdirectory} の処理中にエラーが発生しました: {e}")
                        continue
                else:
                    messagebox.showerror("エラー", f"{subdirectory} は被験者リストで重複しています。")
        # print(f"{success_count} / {total_count} のサブディレクトリの処理が成功しました。")
        """
        2025/05/20 追記
        リストに追加された DataFrame を結合
        作成されたデータフレームを出力
        """
        all_df = pd.concat(all_df_list, ignore_index=True)
        csv_path = Path(self.csv_sheet)
        new_name = csv_path.with_stem(csv_path.stem + '_all_summary')
        print(new_name)
        all_df.to_csv(f'{new_name}', index=False, encoding='shift_jis')
        """
        2025/05/20 追記ここまで
        """

        if(total_count == success_count):
            messagebox.showinfo("成功", "すべてのサマリCSVとPDFレポートが生成されました")
        else:
            messagebox.showinfo("結果", f"{success_count} / {total_count} のサマリCSVとPDFレポートが生成されました")

        self.tx.set(f'処理完了')
        self.status_label.update()

    
    def create_plots_and_save(self, summary_df, target_dir, correction, name=None, age=None):

        print(f"create_plots_and_save START: {target_dir}")
        dirname = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        image_dir = Path(dirname + "/image_file")
        output_dir = Path(dirname + "/output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 名前の入力
        if name is None:
            name = self.name_entry.get()
            if not name:
                name = "テスト"

        # 年齢の入力
        if age is None:
            age = self.age_entry.get()
            if not age:
                age = "20"
            age = int(age)
        
        # グラフの生成とPDF出力
        star_image_path = f'{image_dir}' # 背景画像のパス
        font_path = f'{image_dir}/rounded-mplus-1c-black.ttf' # 日本語フォントのパス
        output_file = f'{output_dir}/output.pdf' # 出力ファイルのパス
        # 各グラフの配置位置 (背景画像の座標系で指定)
        positions = [(530, 700, 530+1080, 700+720), (2750, 650, 2750+1080, 650+720), (1300, 2000, 1300+1080, 2000+720), (2800, 2000, 2800+1080, 2000+720)]
        text_positions = [(595, 150), (50, 280)]


        selected_dir_name = os.path.basename(target_dir)

        # サマリCSVの保存
        summary_df.to_csv(f'{output_dir}/{selected_dir_name}_summary.csv', index=False, encoding='shift_jis')

        # print(correction)
        if correction == "あり":
            # 不要な列を削除
            columns_to_drop = ['歩行Ex', '生活活動Ex', '合計Ex', '歩行時間(秒)', '生活活動時間(秒)', 'SB(秒)', 'LPA(秒)', 'MPA(秒)', 'VPA(秒)', '装着時間(秒)']
            summary_df = summary_df.drop(columns=columns_to_drop)
            # 特定の列名を変更
            summary_df.columns = summary_df.columns.str.replace('0補_', '', regex=False)





        # PDFの作成
        create_plots_on_image(name, age, summary_df, f'{image_dir}', output_dir, selected_dir_name, positions, text_positions, font_path)
        

        
if __name__ == "__main__":
    if hasattr(sys, 'setdefaultencoding'):
        import locale
        lang, enc = locale.getdefaultlocale()
        sys.setdefaultencoding('utf-8')

    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = CSVProcessorApp(root)
    root.mainloop()
