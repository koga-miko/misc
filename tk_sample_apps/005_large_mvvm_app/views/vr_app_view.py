"""VRアプリケーションのトップレベルビューを提供するモジュール"""
import tkinter as tk
from tkinter import ttk
from viewmodels.vr_app_view_model import VrAppViewModel, ScreenType
from views.vr_help_view import VrHelpView

class VrAppView():
    """VrAppViewはアプリケーションのメイン画面を提供する"""
    def __init__(self, root:tk.Tk):
        self.root = root
        self.root.overrideredirect(True) # タイトルバーを非表示にする

        self.sub_window = None  # ヘルプ画面のサブウィンドウを保持するための変数

        # メインウィンドウの設定
        self.top_frame = ttk.Frame(self.root, width=500, height=100)
        self.top_frame.pack(pady=10)

        # ViewModelのインスタンスを作成
        # VrSessionViewModelはModelとViewの間を仲介する役割を持つ
        self.view_model = VrAppViewModel(self.top_frame)

        # ステータスアイコン（ラベル部品使用）を作成
        self.icon_label = ttk.Label(self.top_frame, text=self._get_icon(), font=("Arial", 20), width=3)
        self.icon_label.pack(side="left", padx=5)

        # trace_addを使用してview_modelのステータス変化を監視
        # ステータスが変化したときにアイコンを更新する
        self.view_model.status_var.trace_add("write", lambda *kwargs: self.icon_label.config(text=self._get_icon()))

        # テキストラベルを作成 ※ view_model のテキストに変化に応じて更新される 
        self.text_label = ttk.Label(self.top_frame, textvariable=self.view_model.text_var, font=("Arial", 20), width=20)
        self.text_label.pack(side="left", expand=True, padx=5)

        # 閉じるボタンを作成
        self.close_button = ttk.Button(self.top_frame, text="✖", command=self.view_model.request_abort, width=4)
        self.close_button.pack(side="right", padx=5)

        # trace_addを使用して画面の変化を監視
        self.view_model.screen_name_var.trace_add("write", self._on_change_screen)

    def _get_icon(self):
        """ ステータス変更時に呼び出されるコールバック """
        # アイコン画像の設定（仮）
        self.icons = {
            "initiaizing": "🔄",
            "ready": "🎤",
            "speaking": "🗣️",
            "processing": "🔄",
            "taskend": "💡",
        }
        return self.icons[self.view_model.status_var.get()]

    def _on_change_screen(self, *_):
        """ 画面種別が変化したときに呼び出されるコールバック """
        screen_name = self.view_model.screen_name_var.get()
        # ヘルプ画面
        if screen_name == ScreenType.VR_HELP.name:
            self.sub_window = VrHelpView(self.root)
            self.sub_window.protocol("WM_DELETE_WINDOW", self._destroy_help_view)
        # トップ画面
        elif screen_name == ScreenType.VR_TOP.name:
            self._destroy_help_view()
        # 終了画面（アプリ終了）
        elif screen_name == ScreenType.VR_EXIT.name:
            self.view_model.shutdown()
            self.root.quit()
        else:
            raise ValueError(f"Unknown screen type: {screen_name}")

    def _destroy_help_view(self):
        """ ヘルプ画面を閉じる """
        if self.sub_window is not None:
            self.sub_window.destroy()
            self.sub_window = None

