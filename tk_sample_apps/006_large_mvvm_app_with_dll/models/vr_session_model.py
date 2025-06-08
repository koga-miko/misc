"""VRセッションモデルクラス
このクラスは、音声認識セッションの状態を管理し、ステータスやテキストの変更を通知する機能を提供します。"""
import threading
import time

class VrSessionModel:
    """ VRセッションモデルクラス """
    def __init__(self):
        self.stop_callback = None
        self.screen_callback = None
        self.status_callback = None
        self.text_callback = None
        self.running = False

    def register_on_stopped_model_callback(self, callback):
        """ 機能終了完了コールバック登録 """
        self.stop_callback = callback

    def register_on_changed_screen_callback(self, callback):
        """ ステータス変更コールバック登録 """
        self.screen_callback = callback

    def register_on_changed_status_callback(self, callback):
        """ ステータス変更コールバック登録 """
        self.status_callback = callback

    def register_on_changed_text_callback(self, callback):
        """ テキスト変更コールバック登録 """
        self.text_callback = callback

    def start_vr(self):
        """ 音認ぽい機能の開始要求 """
        self.running = True
        # スレッドで非同期処理を開始
        threading.Thread(target=self._run_process, daemon=True).start()

    def stop_vr(self):
        """ 機能終了要求 """
        self.running = False
        if self.stop_callback:
            self.stop_callback()

    def _run_process(self):
        """ バックグラウンド処理（ステータス変更を通知） """
        # シナリオの定義
        scinario = [
            # status, text, period
            ("Top", "initiaizing", "", 3),
            ("Top", "ready", "ご用件をどうぞ", 2),
            ("Top", "speaking", "(発話中)", 1),
            ("Top", "speaking", "ヘ", 0.2),
            ("Top", "speaking", "ヘル", 0.2),
            ("Top", "speaking", "ヘルプ", 1),
            ("Top", "processing", "ヘルプ", 1),
            ("Help", "ready", "ご用件をどうぞ", 7),
            ("Help", "speaking", "(発話中)", 1.5),
            ("Help", "speaking", "ま", 0.2),
            ("Help", "speaking", "まど", 0.2),
            ("Help", "speaking", "まどを", 0.2),
            ("Help", "speaking", "まどをあ", 0.2),
            ("Help", "speaking", "まどをあけ", 0.2),
            ("Help", "speaking", "まどをあけて", 1),
            ("Help", "speaking", "窓を開けて", 1),
            ("Help", "processing", "窓を開けて", 2),
            ("Help", "taskend", "窓を開けます", 3),
        ]
        previous_screen = ""
        previous_text = ""
        previous_status = ""
        for screen, status, text, period in scinario:
            if not self.running:
                break  # 停止要求があれば中断
            if previous_screen != screen:
                # 画面が変わった場合
                previous_screen = screen
                if self.screen_callback:
                    self.screen_callback(screen)
            if previous_status != status:
                # ステータスが変わった場合
                previous_status = status
                if self.status_callback:
                    self.status_callback(status)
            if previous_text != text:
                # テキストが変わった場合
                previous_text = text
                if self.text_callback:
                    self.text_callback(text)
            time.sleep(period)
        if self.running:
            self.stop_vr()
