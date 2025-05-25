from model import VrModel

class ViewModel:
    """ViewModelはModelとViewの間を仲介する役割を持つ"""
    def __init__(self, model: VrModel):
        self.model = model

        # 初期ステータスとテキストの設定
        self._status = "initiaizing"
        self._text = ""

        # コールバックの初期化
        self.changed_status_callback = None
        self.changed_text_callback = None
        self.on_exit_callback = None

        # Modelのコールバックを登録
        self.model.register_on_changed_status_callback(self.on_changed_status)
        self.model.register_on_changed_text_callback(self.on_changed_text)
        self.model.register_on_stopped_model_callback(self.on_stopped_model)

        # Modelの開始
        self.model.start_vr()

    def request_abort(self):
        """Modelの処理を停止する"""
        self.model.stop_vr()

    def register_changed_status_callback(self, callback: callable):
        """ステータス変更時のコールバックを登録する"""
        self.changed_status_callback = callback

    def register_changed_text_callback(self, callback: callable):
        """テキスト変更時のコールバックを登録する"""
        self.changed_text_callback = callback

    def register_on_exit_callback(self, callback: callable):
        """アプリ終了時のコールバックを登録する"""
        self.on_exit_callback = callback

    @property
    def status(self):
        """現在のステータスを取得"""
        return self._status

    @property
    def text(self):
        """現在のテキストを取得"""
        return self._text

    def on_changed_status(self, status: str):
        """Modelのステータスが変更されたときに呼び出される"""
        self._status = status  # Modelのステータスを更新
        print(f"[ViewModel] Modelがステータス更新しました: {self._status}")
        if self.changed_status_callback:
            self.changed_status_callback(self._status)

    def on_changed_text(self, text: str):
        """Modelのテキストが変更されたときに呼び出される"""
        self._text = text
        print(f"[ViewModel] Modelがテキストを更新しました: {self._text}")
        if self.changed_text_callback:
            self.changed_text_callback(self._text)

    def on_stopped_model(self):
        """Modelの処理が終了したときに呼び出される"""
        print("[ViewModel] 機能が終了しました")
        if self.on_exit_callback:
            self.on_exit_callback()
    