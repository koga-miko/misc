from model import Model
from view import View

def on_status_change(status):
    print(f"Modelがステータス更新しました: {status}")
    view.set_icon(status)

def on_text_change(text):
    print(f"テキスト更新: {text}")
    view.set_text(text)

def on_stop():
    print("機能が終了しました")
    view.stop_app()  # アプリの終了をリクエスト

model = Model()
view = View(on_cancel=model.stop)

model.register_status_callback(on_status_change)
model.register_text_callback(on_text_change)
model.register_stop_callback(on_stop)

model.start()
view.mainloop()  # GUIメインループを開始
