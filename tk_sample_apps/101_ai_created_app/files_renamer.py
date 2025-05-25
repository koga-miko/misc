# files_renamer.py について
# [概要]
# - フォルダ内のテキストをまとめてリネームするGUIアプリ
# [入力]
# - 対象フォルダパス（フォルダピッカーのダイアログを表示させて指定可能）
# - 対象ファイル名の検索パターン（正規表現）
# - リネーム後のファイル名パターン（reモジュールのsubメソッドの置き換え文字列に相当）
# [出力]
# - リスト更新ボタン（押下されたら、入力内容をもとに対象フォルダ内のファイルを検索し、対象ファイルリストとプレビューリストを更新する）
# - 対象ファイルリスト（入力の対象フォルダパスの中で検索パターンにヒットするものを複数行テキストとして表示する）
# - プレビューリスト（上記対象ファイルリストのそれぞれのファイル名が、リネーム後のファイル名パターンに基づいてリネームされた結果を、プレビュー表示するための複数行テキスト表示する）
# - リネーム実行ボタン（押下されたら実際にリネームを実行する。
# [注意点]
# - 対象フォルダパスは、必ず存在するフォルダを指定すること
# - 対象ファイル名の検索パターンは、正規表現で指定すること
# - リネーム後のファイル名パターンは、正規表現で指定すること
# - リネーム実行ボタンを押下する前に、必ずプレビューリストを確認すること
# - リネーム実行ボタンを押下すると、実際にファイル名が変更されるので注意すること
# - リネーム実行ボタンを押下した後は、元に戻すことはできないので注意すること

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
class FilesRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("Files Renamer")

        # フォルダパス入力
        self.folder_path = tk.StringVar()
        tk.Label(root, text="対象フォルダパス:").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(root, textvariable=self.folder_path, width=50).grid(row=0, column=1)
        tk.Button(root, text="フォルダ選択", command=self.select_folder).grid(row=0, column=2)

        # 検索パターン入力
        self.search_pattern = tk.StringVar()
        tk.Label(root, text="検索パターン:").grid(row=1, column=0, sticky=tk.W)
        tk.Entry(root, textvariable=self.search_pattern, width=50).grid(row=1, column=1)

        # リネーム後のファイル名パターン入力
        self.rename_pattern = tk.StringVar()
        tk.Label(root, text="リネーム後のファイル名パターン:").grid(row=2, column=0, sticky=tk.W)
        tk.Entry(root, textvariable=self.rename_pattern, width=50).grid(row=2, column=1)

        # リスト更新ボタン
        tk.Button(root, text="リスト更新", command=self.update_list).grid(row=3, columnspan=3)

        # 対象ファイルリスト
        self.file_list_text = tk.Text(root, height=10, width=80)
        self.file_list_text.grid(row=4, columnspan=3)

        # プレビューリスト
        self.preview_list_text = tk.Text(root, height=10, width=80)
        self.preview_list_text.grid(row=5, columnspan=3)

        # リネーム実行ボタン
        tk.Button(root, text="リネーム実行", command=self.rename_files).grid(row=6, columnspan=3)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def update_list(self):
        folder = self.folder_path.get()
        search_pattern = self.search_pattern.get()
        
        if not os.path.isdir(folder):
            messagebox.showerror("エラー", "指定されたフォルダが存在しません。")
            return
        if not search_pattern:
            messagebox.showerror("エラー", "検索パターンを入力してください。")
            return
        try:
            regex = re.compile(search_pattern)
        except re.error:
            messagebox.showerror("エラー", "正規表現のパターンが無効です。")
            return
        self.file_list_text.delete(1.0, tk.END)
        self.preview_list_text.delete(1.0, tk.END)
        files = os.listdir(folder)
        matched_files = [f for f in files if regex.search(f)]
        if not matched_files:
            messagebox.showinfo("情報", "一致するファイルがありません。")
            return
        self.file_list_text.insert(tk.END, "\n".join(matched_files))
        rename_pattern = self.rename_pattern.get()
        for f in matched_files:
            new_name = regex.sub(rename_pattern, f)
            self.preview_list_text.insert(tk.END, f"{f} -> {new_name}\n")

    def rename_files(self):
        folder = self.folder_path.get()
        search_pattern = self.search_pattern.get()
        rename_pattern = self.rename_pattern.get()

        if not os.path.isdir(folder):
            messagebox.showerror("エラー", "指定されたフォルダが存在しません。")
            return
        if not search_pattern:
            messagebox.showerror("エラー", "検索パターンを入力してください。")
            return
        try:
            regex = re.compile(search_pattern)
        except re.error:
            messagebox.showerror("エラー", "正規表現のパターンが無効です。")
            return

        files = os.listdir(folder)
        matched_files = [f for f in files if regex.search(f)]
        if not matched_files:
            messagebox.showinfo("情報", "一致するファイルがありません。")
            return

        for f in matched_files:
            new_name = regex.sub(rename_pattern, f)
            old_path = os.path.join(folder, f)
            new_path = os.path.join(folder, new_name)
            os.rename(old_path, new_path)

        messagebox.showinfo("成功", "ファイル名の変更が完了しました。") 
        self.update_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = FilesRenamer(root)
    root.mainloop()
    

