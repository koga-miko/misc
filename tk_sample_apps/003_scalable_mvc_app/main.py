from model import VrModel
from view import View
from controller import Controller

def main():
    """アプリケーションのエントリーポイント"""
    model = VrModel()
    view = View()
    Controller(model, view)

    # GUIメインループを開始
    view.mainloop()

if __name__ == "__main__":
    main()
