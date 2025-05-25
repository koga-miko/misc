# small_app.py について
# [概要]
# - TKinterを使用して、1つの画面を持つ小さなアプリケーションを作成する。
# - このアプリケーションは、TKinterの代表的な部品を説明するためのものである。
# - 画面上には、ラベル、ボタン、テキスト入力欄、チェックボックス、ラジオボタン、リストボックスを配置する。
import tkinter as tk
from tkinter import messagebox

def show_text():
    input_text = entry.get()
    label.config(text=input_text)

# メインウィンドウの作成
root = tk.Tk()
root.title("Small App")
root.geometry("400x600")

# ラベルの作成
label = tk.Label(root, text="ここにテキストが表示されます", font=("Arial", 14))
label.pack(pady=10)

# テキスト入力欄の作成
entry = tk.Entry(root, font=("Arial", 14))
entry.pack(pady=10)

# ボタンの作成
button = tk.Button(root, text="表示", command=show_text, font=("Arial", 14))
button.pack(pady=10)

# チェックボックスの作成
checkbox_var = tk.BooleanVar()
checkbox = tk.Checkbutton(root, text="チェックボックス", variable=checkbox_var, font=("Arial", 14))
checkbox.pack(pady=10)

# ラジオボタンの作成
radio_var = tk.StringVar(value="option1")
radio1 = tk.Radiobutton(root, text="オプション1", variable=radio_var, value="option1", font=("Arial", 14))
radio1.pack(pady=5)
radio2 = tk.Radiobutton(root, text="オプション2", variable=radio_var, value="option2", font=("Arial", 14))
radio2.pack(pady=5)

# リストボックスの作成
listbox = tk.Listbox(root, font=("Arial", 14))
listbox.pack(pady=10)
# リストボックスに項目を追加
for item in ["項目1", "項目2", "項目3", "項目4"]:
    listbox.insert(tk.END, item)

# リストボックスの選択状態を確認するための関数
def show_selected_item():
    selected_items = listbox.curselection()
    if selected_items:
        selected_text = listbox.get(selected_items[0])
        messagebox.showinfo("選択された項目", f"選択された項目: {selected_text}")
    else:
        messagebox.showwarning("選択なし", "項目が選択されていません")
# リストボックスの選択状態を確認するためのボタン
check_button = tk.Button(root, text="選択項目を確認", command=show_selected_item, font=("Arial", 14))
check_button.pack(pady=10)
# メインループの開始
root.mainloop()
