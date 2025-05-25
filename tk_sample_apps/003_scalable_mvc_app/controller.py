from model import VrModel
from view import View

class Controller:
    """ControllerクラスはModelとViewの間を仲介する役割を持つ"""
    def __init__(self, model: VrModel, view: View):
        self.model = model
        self.view = view

        # コールバックの登録
        self.model.register_status_callback(self.on_status_change)
        self.model.register_text_callback(self.on_text_change)
        self.model.register_stop_callback(self.on_stop)

        # Viewの×ボタンにModelの停止要求を紐付け
        self.view.set_on_cancel(self.model.stop)

        # modelの開始
        print("Controller: Modelを開始します")
        self.model.start()


    def on_status_change(self, status: str):
        """Modelのステータスが変更されたときに呼び出される"""
        print(f"Modelがステータス更新しました: {status}")
        self.view.set_status(status)

    def on_text_change(self, text: str):
        """Modelのテキストが変更されたときに呼び出される"""
        print(f"テキスト更新: {text}")
        self.view.set_text(text)

    def on_stop(self):
        """Modelの停止要求があったときに呼び出される"""
        print("機能が終了しました")
        self.view.stop_app()  # アプリの終了をリクエスト
