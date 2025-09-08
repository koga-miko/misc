""" SafeViewUpdater: ViewModelがViewの更新を安全に行うためのクラス """
import queue
from tkinter import Widget

class SafeViewUpdater:
    """ ViewUpdaterは、ViewModelがViewの更新を安全に行うためのクラスです """
    def __init__(self, widget: Widget):
        self.widget = widget

        # キューを初期化        
        self.queue = queue.Queue()
        self._process_queue()

    def update_view_safety(self, update_vars_func: callable):
        """ Viewの更新を安全に行うためのメソッド """
        self.queue.put(("update_vars_func", update_vars_func))

    def shutdown(self):
        """ SafeViewUpdaterの終了リクエストをキューに追加 """
        self.queue.put(("shutdown", None))

    def _process_queue(self):
        """ キューからメッセージを受け取り、安全にViewを更新 or SafeViewUpdaterを終了 """
        while not self.queue.empty():
            msg_type, value = self.queue.get()
            if msg_type == "update_vars_func":
                update_vars_func = value
                update_vars_func()
            elif msg_type == "shutdown":
                return # `_process_queue()` の再実行を防ぐ

        # キューが空であれば、100ms後に再度キューをチェック
        self.widget.after(100, self._process_queue)
