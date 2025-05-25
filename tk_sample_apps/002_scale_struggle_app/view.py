import tkinter as tk
from tkinter import ttk
import queue
from model import VrModel

class View(tk.Tk):
    """ アプリケーションのビューを定義するクラス """
    def __init__(self, model: VrModel):
        super().__init__()

        self.model = model

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

        # コールバックの登録
        self.model.register_status_callback(self.on_status_change)
        self.model.register_text_callback(self.on_text_change)
        self.model.register_stop_callback(self.on_stop)

        # キューを初期化
        self.queue = queue.Queue()
        self._process_queue()

        self.model.start()  # Modelの処理を開始

    def on_status_change(self, status: str):
        """Modelのステータスが変更されたときに呼び出される"""
        self.queue.put(("status", status))

    def on_text_change(self, text: str):
        """Modelのテキストが変更されたときに呼び出される"""
        self.queue.put(("text", text))

    def on_stop(self):
        """Modelの停止要求があったときに呼び出される"""
        self.queue.put(("exit", None))

    def set_on_cancel(self, callback):
        """ ×ボタンのコールバックを設定 """
        self.on_cancel = callback

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
        self.model.stop()

