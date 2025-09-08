""" VRセッションのViewModelクラス """
import tkinter as tk
from enum import Enum
from viewmodels.safe_view_updater import SafeViewUpdater
from models.vr_session_model import VrSessionModel

class ScreenType(Enum):
    """画面の種類を定義するEnum"""
    VR_TOP = "VR Top"
    VR_HELP = "VR Help"
    VR_EXIT = "VR Exit" # アプリケーション終了画面（これになったらアプリケーションを終了する）

class VrAppViewModel(SafeViewUpdater):
    """ViewModelはModelとViewの間を仲介する役割を持つ"""
    def __init__(self, root: tk):
        super().__init__(root)
        # Modelのインスタンスを作成
        self.model = VrSessionModel()

        # コールバックの初期化
        self.on_exit_callback = None

        # screen_nameの初期設定
        self._screen_name_var = tk.StringVar()
        self._screen_name_var.set(ScreenType.VR_TOP.name)

        # ステータスの初期設定
        self._status_var = tk.StringVar()
        self._status_var.set("initiaizing")

        # テキストの初期設定
        self._text_var = tk.StringVar()
        self._text_var.set("")

        # Modelのコールバックを登録
        self.model.register_on_changed_screen_callback(self._on_changed_screen)
        self.model.register_on_changed_status_callback(self._on_changed_status)
        self.model.register_on_changed_text_callback(self._on_changed_text)
        self.model.register_on_stopped_model_callback(self._on_stopped_model)

        # Modelの開始
        self.model.start_vr()

    @property
    def screen_name_var(self):
        """現在のテキストを取得"""
        return self._screen_name_var

    @property
    def status_var(self):
        """現在のステータスを取得"""
        return self._status_var

    @property
    def text_var(self):
        """現在のテキストを取得"""
        return self._text_var

    def request_abort(self):
        """Modelの処理を停止する"""
        self.model.stop_vr()

    def _on_changed_screen(self, screen: str):
        """Modelの画面種別が変更されたときに呼び出される"""
        screen_name = ""
        if screen == "Top":
            screen_name = ScreenType.VR_TOP.name
        elif screen == "Help":
            screen_name = ScreenType.VR_HELP.name
        self.update_view_safety(
            lambda : self._screen_name_var.set(screen_name),
        )

    def _on_changed_status(self, status: str):
        """Modelのステータスが変更されたときに呼び出される"""
        self.update_view_safety(
            lambda : self._status_var.set(status),
        )

    def _on_changed_text(self, text: str):
        """Modelのテキストが変更されたときに呼び出される"""
        self.update_view_safety(
            lambda : self._text_var.set(text),
        )

    def _on_stopped_model(self):
        """Modelの処理が終了したときにアプリケーションを終了する"""
        self.update_view_safety(
            lambda : self._screen_name_var.set(ScreenType.VR_EXIT.name),
        )
