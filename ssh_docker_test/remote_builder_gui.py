# Description: ビルド管理ツールのGUIを作成する

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from remote_builder import RemoteBuilder
class RemoteBuilderGUI:
    def __init__(self):
        self.rmt_bldr = RemoteBuilder("./build_config.yaml")
        self.root = tk.Tk()
        self.root.title("ビルド管理ツール")
        self.root.geometry("600x400")
        self.create_widgets()
    
    def create_widgets(self):
        tk.Label(self.root, text="リリースバージョン:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.release_version = tk.Entry(self.root, width=50)
        self.release_version.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.root, text="baselineのブランチ名:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.branch_name = tk.Entry(self.root, width=50)
        self.branch_name.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.root, text="仕向け品番:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.product_list = ttk.Combobox(self.root, values=[region['name'] for region in self.rmt_bldr['regions']], width=47)
        self.product_list.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(self.root, text="ビルドの実行ステータス:").grid(row=7, column=0, sticky=tk.W, padx=10, pady=5)
        self.status_text = scrolledtext.ScrolledText(self.root, width=50, height=10)
        self.status_text.grid(row=3, column=1, padx=10, pady=5)
        
        self.run_button = tk.Button(self.root, text="ビルド準備", command=self.prepare_build)
        self.run_button.grid(row=4, column=0, padx=10, pady=10)

        self.run_button = tk.Button(self.root, text="ビルド実行", command=self.run_build)
        self.run_button.grid(row=4, column=1, padx=10, pady=10)

        self.cancel_button = tk.Button(self.root, text="ビルドキャンセル", command=self.cancel_build)
        self.cancel_button.grid(row=4, column=2, padx=10, pady=10)

    def run_build(self):
        # 各TextBoxや選択リストの情報を取得
        config = self.config_path.get()
        version = self.release_version.get()
        branch = self.branch_name.get()
        product = self.product_list.get()

        # 取得した情報をビルド実行ステータスに表示
        self.status_text.insert(tk.END, f"ビルド用設定ファイルのパス: {config}\n")
        self.status_text.insert(tk.END, f"リリースバージョン: {version}\n")
        self.status_text.insert(tk.END, f"baselineのブランチ名: {branch}\n")
        self.status_text.insert(tk.END, f"仕向け品番: {product}\n")
        self.status_text.insert(tk.END, "ビルドを実行中...\n")

        self.run_button.config(state=tk.DISABLED)

        # ビルドが完了したらボタンを有効化
        self.root.after(100000, self.enable_run_button)

    def enable_run_button(self):
        self.run_button.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, "ビルドが完了しました。\n")

    def cancel_build(self):
        self.status_text.insert(tk.END, "ビルドをキャンセルしました。\n")
        threading.Thread(target=self.delayed_enable_run_button).start()

    def delayed_enable_run_button(self):
        time.sleep(10)
        self.root.after(0, self.enable_run_button)

    def show(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = RemoteBuilderGUI()
    gui.show() # メインループを開始

    