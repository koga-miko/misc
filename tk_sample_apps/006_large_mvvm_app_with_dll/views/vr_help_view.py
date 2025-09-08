"""VRヘルプビューの実装"""
import tkinter as tk
from tkinter import ttk
from viewmodels.vr_help_view_model import VrHelpViewModel

class VrHelpView(tk.Toplevel):
    """VrHelpViewはアプリケーションのヘルプ画面を提供する"""
    def __init__(self, root:tk.Tk):
        super().__init__(root)
        self.title("VRヘルプ")
        self.geometry("250x300")
        self.frame = ttk.Frame(self, width=250, height=300)
        self.frame.pack()

        self.view_model = VrHelpViewModel(self.frame)

        # 常時表示のヘルプ内容を表示するラベルを作成
        self.help_required_text = (
            "発話可能コマンド（例） \n"
            "- 今日の天気は？ \n"
            "- 今日のニュースは？ \n"
            "- 今日の予定は？ \n"
            "- 今日の占いは？ \n"
            "- 今日の日没時間は？ \n"
        )
        self.required_label = ttk.Label(self.frame, text=self.help_required_text, justify=tk.LEFT)
        self.required_label.pack(padx=10, pady=10)

        # 車両機能用ヘルプが表示される場合のラベルを作成
        self.help_optional_text = (
            "- 窓を開けて \n"
            "- 温度を上げて \n"
            "- 温度を下げて \n"
        )
        self.optional_label = ttk.Label(self.frame, text=self.help_optional_text, justify=tk.LEFT)
        # 車両機能用ヘルプが表示されるかどうかの変化を監視
        self.view_model.vehicle_available_var.trace_add( "write", self.update_optional_help)

    def update_optional_help(self, *args):
        """車両機能用ヘルプの表示を更新"""
        is_available = self.view_model.vehicle_available_var.get()
        # 車両機能用ヘルプが表示される場合はラベルを表示、そうでない場合は非表示にする
        if is_available:
            self.optional_label.pack()
        else:
            self.optional_label.pack_forget()
