import tkinter as tk
from tkinter import ttk
import queue
from view_model import ViewModel 

class View(tk.Tk):
    def __init__(self, view_model: ViewModel, on_cancel=None):
        super().__init__()
        self.view_model = view_model
        self.overrideredirect(True) # タイトルバーを非表示にする

        self.frame = ttk.Frame(self, width=500, height=100)
        self.frame.pack()

        self.on_cancel = on_cancel  # ×ボタンの非同期コールバック

        # アイコン画像の設定（仮）
        self.icons = {
            "initiaizing": "🔄",
            "ready": "🎤",
            "speaking": "🗣️",
            "processing": "🔄",
            "taskend": "💡",
        }

        self.icon_var = tk.StringVar()
        self.icon_var.set(self.icons[self.view_model.status])  # 初期アイコンを設定
        self.icon_label = ttk.Label(self.frame, textvariable=self.icon_var, font=("Arial", 20), width=3)
        self.icon_label.pack(side="left", padx=5)

        self.text_var = tk.StringVar()
        self.text_var.set(self.view_model.text)  # 初期テキストを設定
        self.text_label = ttk.Label(self.frame, textvariable=self.text_var, font=("Arial", 20), width=20)
        self.text_label.pack(side="left", expand=True, padx=5)

        self.close_button = ttk.Button(self.frame, text="✖", command=self.view_model.request_abort, width=4)
        self.close_button.pack(side="right", padx=5)

        self.frame.pack(padx=10, pady=10)

        self.view_model.register_changed_status_callback(self.changed_status)
        self.view_model.register_changed_text_callback(self.changed_text)
        self.view_model.register_on_exit_callback(self.exit)

        # キューを初期化        
        self.queue = queue.Queue()
        self._process_queue()

    def changed_status(self, state):
        """ ステータス変更時に呼び出されるコールバック """
        self.queue.put(("status", state))

    def changed_text(self, text):
        """ テキスト変更時に呼び出されるコールバック """
        self.queue.put(("text", text))

    def exit(self):
        """ アプリの終了リクエストをキューに追加 """
        self.queue.put(("exit", None))

    def _process_queue(self):
        """ キューからメッセージを受け取り、安全にGUIを更新 or アプリ終了 """
        while not self.queue.empty():
            msg_type, value = self.queue.get()
            if msg_type == "status" and value in self.icons:
                self.icon_var.set(self.icons[value])
            elif msg_type == "text":
                self.text_var.set(value)
            elif msg_type == "exit":  # アプリ終了処理
                self.quit()
                return  # `_process_queue()` の再実行を防ぐ

        self.frame.after(100, self._process_queue)  # 100msごとにキューをチェック
