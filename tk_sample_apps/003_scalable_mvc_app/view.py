import tkinter as tk
from tkinter import ttk
import queue

class View(tk.Tk):
    """ アプリケーションのビューを定義するクラス """
    def __init__(self):
        super().__init__()
        self.overrideredirect(True) # タイトルバーを非表示にする
        self.frame = ttk.Frame(self, width=500, height=100)
        self.frame.pack()
        self.on_cancel = None  # ×ボタンの非同期コールバック
        
        # アイコン画像の設定（仮）
        self.icons = {
            "initiaizing": "🔄",
            "ready": "🎤",
            "speaking": "🗣️",
            "processing": "🔄",
            "taskend": "💡",
        }

        self.icon_label = ttk.Label(self.frame, text="", font=("Arial", 20), width=3)
        self.icon_label.pack(side="left", padx=5)

        self.text_label = ttk.Label(self.frame, text="", font=("Arial", 20), width=20)
        self.text_label.pack(side="left", expand=True, padx=5)

        self.close_button = ttk.Button(self.frame, text="✖", command=self.on_close, width=4)
        self.close_button.pack(side="right", padx=5)

        self.frame.pack(padx=10, pady=10)

        self.queue = queue.Queue()
        self._process_queue()

    def set_status(self, status):
        """ アイコン更新リクエストをキューに追加 """
        self.queue.put(("status", status))

    def set_text(self, text):
        """ テキスト更新リクエストをキューに追加 """
        self.queue.put(("text", text))
    
    def set_on_cancel(self, callback):
        """ ×ボタンのコールバックを設定 """
        self.on_cancel = callback

    def stop_app(self):
        """ アプリの終了リクエストをキューに追加 """
        self.queue.put(("exit", None))

    def _process_queue(self):
        """ キューからメッセージを受け取り、安全にGUIを更新 or アプリ終了 """
        while not self.queue.empty():
            msg_type, value = self.queue.get()
            if msg_type == "status" and value in self.icons:
                self.icon_label.config(text=self.icons[value])
            elif msg_type == "text":
                self.text_label.config(text=value)
            elif msg_type == "exit":  # アプリ終了処理
                self.quit()
                return  # `_process_queue()` の再実行を防ぐ

        self.frame.after(100, self._process_queue)  # 100msごとにキューをチェック

    def on_close(self):
        """ ×ボタンが押されたときの処理 """
        if self.on_cancel:
            self.on_cancel()
