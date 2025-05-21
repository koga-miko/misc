import tkinter as tk
from tkinter import ttk
import threading
import queue
import time

class View:
    def __init__(self, on_cancel=None):
        self.root = tk.Tk()
        self.root.overrideredirect(True)

        self.frame = ttk.Frame(self.root, width=400)
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

        self.icon_label = ttk.Label(self.frame, text="", font=("Arial", 20), width=3)
        self.icon_label.pack(side="left", padx=5)

        self.text_label = ttk.Label(self.frame, text="", font=("Arial", 20), width=20)
        self.text_label.pack(side="left", expand=True, padx=5)

        self.close_button = ttk.Button(self.frame, text="✖", command=self.on_close, width=4)
        self.close_button.pack(side="right", padx=5)

        self.frame.pack(padx=10, pady=10)

        self.queue = queue.Queue()
        self._process_queue()

    def mainloop(self):
        self.root.mainloop()

    def set_icon(self, state):
        """ アイコン更新リクエストをキューに追加 """
        self.queue.put(("icon", state))

    def set_text(self, text):
        """ テキスト更新リクエストをキューに追加 """
        self.queue.put(("text", text))

    def stop_app(self):
        """ アプリの終了リクエストをキューに追加 """
        self.queue.put(("exit", None))

    def _process_queue(self):
        """ キューからメッセージを受け取り、安全にGUIを更新 or アプリ終了 """
        while not self.queue.empty():
            msg_type, value = self.queue.get()
            if msg_type == "icon" and value in self.icons:
                self.icon_label.config(text=self.icons[value])
            elif msg_type == "text":
                self.text_label.config(text=value)
            elif msg_type == "exit":  # アプリ終了処理
                self.root.quit()
                return  # `_process_queue()` の再実行を防ぐ

        self.frame.after(100, self._process_queue)  # 100msごとにキューをチェック

    def on_close(self):
        """ ×ボタンが押されたときの処理 """
        if self.on_cancel:
            self.on_cancel()

if __name__ == "__main__":

    # 使用例
    def on_cancel():
        print("×ボタンが押されました！（別スレッドで処理中）")

    # 別スレッドからの更新テスト
    def background_task(view):
        view.set_icon("initiaizing")
        view.set_text("初期化中")
        time.sleep(4)
        view.set_icon("ready")
        view.set_text("準備できています")
        time.sleep(4)
        view.set_icon("speaking")
        view.set_text("発話中")
        time.sleep(4)
        view.set_icon("processing")
        view.set_text("処理中")
        time.sleep(4)
        view.set_icon("taskend")
        view.set_text("タスク終了")
        time.sleep(4)
        view.stop_app()  # アプリの終了をリクエスト

    view = View(on_cancel=on_cancel)

    # 別スレッドでの処理を模擬
    threading.Thread(target=background_task, args=(view,), daemon=True).start()

    view.mainloop()

