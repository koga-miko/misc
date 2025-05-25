import threading
import time

class VrModel:
    """Modelクラスはアプリケーションのビジネスロジックを担当します"""
    def __init__(self):
        self.stop_callback = None
        self.status_callback = None
        self.text_callback = None
        self.running = False

    def register_stop_callback(self, callback):
        """ 機能終了完了コールバック登録 """
        self.stop_callback = callback

    def register_status_callback(self, callback):
        """ ステータス変更コールバック登録 """
        self.status_callback = callback

    def register_text_callback(self, callback):
        """ テキスト変更コールバック登録 """
        self.text_callback = callback

    def start(self):
        """ 機能開始要求 """
        if self.running:
            return  # すでに開始済みの場合は何もしない
        self.running = True

        # スレッドで非同期処理を開始
        threading.Thread(target=self._run_process, daemon=True).start()

    def stop(self):
        """ 機能終了要求 """
        self.running = False
        if self.stop_callback:
            self.stop_callback()

    def _run_process(self):
        """ バックグラウンド処理（ステータス変更を通知） """
        scinario = [
            # status, text, period
            ("initiaizing", "", 3),
            ("ready", "ご用件をどうぞ", 5),
            ("speaking", "(発話中)", 1.5),
            ("speaking", "ま", 0.2),
            ("speaking", "まど", 0.2),
            ("speaking", "まどを", 0.2),
            ("speaking", "まどをあ", 0.2),
            ("speaking", "まどをあけ", 0.2),
            ("speaking", "まどをあけて", 1),
            ("speaking", "窓を開けて", 2),
            ("processing", "窓を開けて", 4),
            ("taskend", "窓を開けます", 4),
        ]
        for status, text, period in scinario:
            if not self.running:
                break  # 停止要求があれば中断
            if self.status_callback:
                self.status_callback(status)
            if self.text_callback:
                self.text_callback(text)
            time.sleep(period)
        if self.running:
            self.stop()  # 最後に終了処理を呼び出す
